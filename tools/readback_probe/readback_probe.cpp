// readback_probe.cpp — A4 "readback-probe" discrimination harness.
//
// ASTRA HARNESS SPEC (Q3), followed exactly:
//   Headless standalone (no swapchain, no window). One preallocated source
//   image, one PERSISTENTLY MAPPED host-cached staging buffer. Everything
//   reused across iterations. BUFFER->BUFFER copies first, then the real
//   IMAGE->BUFFER copy. Valid copy->host-visibility dependency (fence on THAT
//   submission), wait on that fence, invalidate the mapped range if
//   noncoherent. ONE CONTINUOUS MONOTONIC WALL-CLOCK TIMELINE per iteration:
//   request -> submission entry/return -> fence-wait entry/return ->
//   invalidate entry/return -> first CPU read -> completed memcpy into
//   ordinary RAM -> completed swizzle in ordinary RAM -> consumer receipt.
//   GPU timestamps around the copy retrieved after completion. Allocation/map
//   and teardown timed separately.
//
// VARIATION MATRIX (Astra rows 1-5):
//   1. cold (first use) vs warm (repeated reuse)          -> init/first-touch/residency
//   2. 4 bytes vs 8.3 MB                                   -> fixed overhead vs transfer work
//   3. copy+completion with NO CPU data access             -> submission/GPU/dependency/scheduling
//   4. first read / bulk memcpy / RAM-only swizzle split   -> mapped access vs conversion/publication
//   5. idle device vs queued backlog                       -> backlog/synchronization
// Plus Astra's decisive-signature probes:
//   - witness job: independent, resource-independent copy on a SECOND queue,
//     fence-polled during the readback wait -> true device-wide stall vs
//     readback-path-specific delay.
//   - residency pressure: fill a large slice of VRAM with resident buffers and
//     re-touch every iteration -> paging (residency/page-table) signature.
//
// Output: per-iteration CSV (raw, continuous ns timeline from process start)
// and summary.md (median/max per timeline segment per cell).

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#define _CRT_SECURE_NO_WARNINGS
#include <windows.h>
#include <vulkan/vulkan.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <vector>
#include <algorithm>

// ---------------------------------------------------------------- timing --
static double g_nsPerTick;
static long long g_t0Tick;
static void timeInit() {
    LARGE_INTEGER f, c;
    QueryPerformanceFrequency(&f);
    QueryPerformanceCounter(&c);
    g_nsPerTick = 1e9 / (double)f.QuadPart;
    g_t0Tick = c.QuadPart;
}
static double nowNs() {
    LARGE_INTEGER c;
    QueryPerformanceCounter(&c);
    return (double)(c.QuadPart - g_t0Tick) * g_nsPerTick;
}

#define VKC(x) do { VkResult r_ = (x); if (r_ != VK_SUCCESS) { \
    fprintf(stderr, "FATAL: VkResult=%d at %s:%d: %s\n", (int)r_, __FILE__, __LINE__, #x); exit(2);} } while(0)

// ------------------------------------------------------- timeline markers --
enum {
    T_REQUEST = 0,      // entry to the pull
    T_SUBMIT_ENTRY,     // vkQueueSubmit (readback) entry
    T_SUBMIT_RETURN,    // vkQueueSubmit (readback) return
    T_FWAIT_ENTRY,      // fence-wait entry
    T_FWAIT_RETURN,     // fence-wait return (host-visible dependency satisfied)
    T_INV_ENTRY,        // vkInvalidateMappedMemoryRanges entry
    T_INV_RETURN,       // invalidate return
    T_FIRST_READ,       // first CPU read of mapped memory
    T_MEMCPY_DONE,      // bulk memcpy into ordinary RAM completed
    T_SWIZZLE_DONE,     // RAM-only swizzle completed
    T_CONSUMER,         // consumer receipt (hash of swizzled RAM)
    T_GPU_RET,          // GPU timestamps retrieved
    T_BSUB_ENTRY,       // backlog submit entry
    T_BSUB_RETURN,      // backlog submit return
    T_WSUB_ENTRY,       // witness submit entry
    T_WSUB_RETURN,      // witness submit return
    T_WSIG,             // witness fence first observed signaled
    T_COUNT
};
static const char* TNAME[T_COUNT] = {
    "request", "submit_entry", "submit_return", "fwait_entry", "fwait_return",
    "invalidate_entry", "invalidate_return", "first_read", "memcpy_done",
    "swizzle_done", "consumer", "gpu_ts_retrieved",
    "backlog_submit_entry", "backlog_submit_return",
    "witness_submit_entry", "witness_submit_return", "witness_first_signaled"
};

struct Iter {
    int idx;
    bool cold;
    double t[T_COUNT];
    double gpu0ns, gpu1ns;   // raw device timestamps converted to ns
    bool wAlreadyDone;       // witness fence already signaled at first poll
    bool wSaw;
};

// ------------------------------------------------------------- constants --
static const VkDeviceSize IMG_BYTES = 1920ull * 1080ull * 4ull; // 8,294,400 ~ 8.3 MB
static const uint32_t IMG_W = 1920, IMG_H = 1080;

// -------------------------------------------------------------- vulkan ----
static VkInstance g_inst;
static VkPhysicalDevice g_pdev;
static VkDevice g_dev;
static VkQueue g_q0, g_q1;
static uint32_t g_famG = 0, g_q0idx = 0, g_q1idx = 0;
static VkPhysicalDeviceProperties g_pdprops;
static VkPhysicalDeviceMemoryProperties g_memprops;
static VkPhysicalDeviceLimits g_limits;
static double g_tsPeriodNs = 1.0;
static bool g_hasReBAR = false;

static VkBuffer g_srcBuf;   // device-local, 8.3 MB (buffer->buffer source)
static VkDeviceMemory g_srcBufMem;
static VkBuffer g_staging;  // persistent, host-cached mapped
static VkDeviceMemory g_stagingMem;
static void* g_stagingPtr;
static bool g_stagingCoherent = false;
static VkMappedMemoryRange g_invRange{};

static VkImage g_imgBig;    // 1920x1080 RGBA8 TRANSFER_SRC
static VkDeviceMemory g_imgBigMem;
static VkImage g_img1x1;    // 1x1 RGBA8 TRANSFER_SRC (the 4-byte image cell)
static VkDeviceMemory g_img1x1Mem;
static VkBuffer g_fillStaging; // host-visible upload buffer
static VkDeviceMemory g_fillStagingMem;

static VkCommandPool g_cmdPool;
static VkCommandBuffer g_cmdMain, g_cmdBacklog, g_cmdWitness, g_cmdTouch;
static VkFence g_fenceMain, g_fenceBacklog, g_fenceWitness, g_fenceTouch;
static VkQueryPool g_queryPool; // 2 timestamps around the copy

// backlog workload (independent device-local buffers, queue serialization row)
struct BlkPair { VkBuffer a, b; VkDeviceMemory ma, mb; };
static std::vector<BlkPair> g_backlog;
static VkDeviceSize g_backlogPairBytes = 0;

// residency-pressure chunks
struct PressChunk { VkBuffer b; VkDeviceMemory m; };
static std::vector<PressChunk> g_press;
static VkDeviceSize g_pressTotal = 0;

// host-side ordinary RAM destinations (reused; allocated once)
static std::vector<uint8_t> g_ramA, g_ramB;
static volatile uint64_t g_sink = 0;

static int findMemType(VkMemoryPropertyFlags want, VkMemoryPropertyFlags forbid) {
    for (uint32_t i = 0; i < g_memprops.memoryTypeCount; ++i) {
        VkMemoryPropertyFlags p = g_memprops.memoryTypes[i].propertyFlags;
        if ((p & want) == want && (p & forbid) == 0) return (int)i;
    }
    return -1;
}

static void allocBuffer(VkDeviceSize size, VkBufferUsageFlags usage, int memType,
                        VkBuffer* buf, VkDeviceMemory* mem) {
    VkBufferCreateInfo bi{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
    bi.size = size; bi.usage = usage; bi.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    VKC(vkCreateBuffer(g_dev, &bi, nullptr, buf));
    VkMemoryRequirements mr;
    vkGetBufferMemoryRequirements(g_dev, *buf, &mr);
    VKC(vkAllocateMemory(g_dev, &(VkMemoryAllocateInfo{
        VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, nullptr, mr.size,
        (uint32_t)memType}), nullptr, mem));
    VKC(vkBindBufferMemory(g_dev, *buf, *mem, 0));
}

static void allocImage(uint32_t w, uint32_t h, int memType,
                       VkImage* img, VkDeviceMemory* mem) {
    VkImageCreateInfo ii{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};
    ii.imageType = VK_IMAGE_TYPE_2D;
    ii.format = VK_FORMAT_R8G8B8A8_UNORM;
    ii.extent = {w, h, 1};
    ii.mipLevels = 1; ii.arrayLayers = 1;
    ii.samples = VK_SAMPLE_COUNT_1_BIT;
    ii.tiling = VK_IMAGE_TILING_OPTIMAL;
    ii.usage = VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT;
    ii.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    ii.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    VKC(vkCreateImage(g_dev, &ii, nullptr, img));
    VkMemoryRequirements mr;
    vkGetImageMemoryRequirements(g_dev, *img, &mr);
    VKC(vkAllocateMemory(g_dev, &(VkMemoryAllocateInfo{
        VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, nullptr, mr.size,
        (uint32_t)memType}), nullptr, mem));
    VKC(vkBindImageMemory(g_dev, *img, *mem, 0));
}

static void submitAndWait(VkQueue q, VkCommandBuffer cmd, VkFence fence) {
    VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
    si.commandBufferCount = 1; si.pCommandBuffers = &cmd;
    VKC(vkQueueSubmit(q, 1, &si, fence));
    VKC(vkWaitForFences(g_dev, 1, &fence, VK_TRUE, UINT64_MAX));
    vkResetFences(g_dev, 1, &fence);
}

static void initVulkan() {
    VkApplicationInfo ai{VK_STRUCTURE_TYPE_APPLICATION_INFO};
    ai.pApplicationName = "readback_probe";
    ai.apiVersion = VK_API_VERSION_1_1;
    VkInstanceCreateInfo ii{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
    ii.pApplicationInfo = &ai;
    // headless: NO surface extensions, NO swapchain anywhere
    VKC(vkCreateInstance(&ii, nullptr, &g_inst));

    uint32_t n = 0;
    VKC(vkEnumeratePhysicalDevices(g_inst, &n, nullptr));
    std::vector<VkPhysicalDevice> pdevs(n == 0 ? 1 : n);
    VKC(vkEnumeratePhysicalDevices(g_inst, &n, pdevs.data()));
    g_pdev = pdevs[0];
    for (uint32_t i = 0; i < n; ++i) {
        VkPhysicalDeviceProperties p;
        vkGetPhysicalDeviceProperties(pdevs[i], &p);
        if (p.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU) { g_pdev = pdevs[i]; break; }
    }
    vkGetPhysicalDeviceProperties(g_pdev, &g_pdprops);
    vkGetPhysicalDeviceMemoryProperties(g_pdev, &g_memprops);
    g_limits = g_pdprops.limits;
    g_tsPeriodNs = (double)g_limits.timestampPeriod;

    uint32_t famCount = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(g_pdev, &famCount, nullptr);
    std::vector<VkQueueFamilyProperties> fams(famCount);
    vkGetPhysicalDeviceQueueFamilyProperties(g_pdev, &famCount, fams.data());
    for (uint32_t i = 0; i < famCount; ++i)
        if (fams[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) { g_famG = i; break; }
    g_q0idx = 0;
    g_q1idx = (fams[g_famG].queueCount >= 2) ? 1 : 0; // second queue of same family

    float prio = 1.0f;
    VkDeviceQueueCreateInfo qci[1]{};
    qci[0].sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
    qci[0].queueFamilyIndex = g_famG;
    qci[0].queueCount = fams[g_famG].queueCount;
    qci[0].pQueuePriorities = &prio;
    VkDeviceCreateInfo di{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
    di.queueCreateInfoCount = 1;
    di.pQueueCreateInfos = qci;
    VKC(vkCreateDevice(g_pdev, &di, nullptr, &g_dev));
    vkGetDeviceQueue(g_dev, g_famG, g_q0idx, &g_q0);
    vkGetDeviceQueue(g_dev, g_famG, g_q1idx, &g_q1);

    // ReBAR signature: a host-visible memory type that lives in the
    // device-local heap
    for (uint32_t i = 0; i < g_memprops.memoryTypeCount; ++i) {
        VkMemoryPropertyFlags p = g_memprops.memoryTypes[i].propertyFlags;
        uint32_t heap = g_memprops.memoryTypes[i].heapIndex;
        if ((p & VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT) &&
            (g_memprops.memoryHeaps[heap].flags & VK_MEMORY_HEAP_DEVICE_LOCAL_BIT))
            g_hasReBAR = true;
    }
}

struct SetupStats {
    double stagingAllocNs, stagingMapNs;
    double srcAllocNs, imgAllocNs, fillSubmitNs;
    int stagingType;
    bool coherent;
} g_setup;

static void createResources() {
    // ---- staging: PERSISTENTLY MAPPED, host-CACHED, prefer NON-coherent so
    // vkInvalidateMappedMemoryRanges is a real step in the dependency chain
    double e = nowNs();
    int typeCachedNoCoherent = findMemType(
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_CACHED_BIT,
        VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    int typeCachedCoherent = findMemType(
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_CACHED_BIT, 0);
    int typeVisible = findMemType(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT, 0);
    int type = typeCachedNoCoherent >= 0 ? typeCachedNoCoherent :
               (typeCachedCoherent >= 0 ? typeCachedCoherent : typeVisible);
    g_setup.stagingType = type;
    g_setup.coherent = (g_memprops.memoryTypes[type].propertyFlags & VK_MEMORY_PROPERTY_HOST_COHERENT_BIT) != 0;
    allocBuffer(IMG_BYTES, VK_BUFFER_USAGE_TRANSFER_DST_BIT, type, &g_staging, &g_stagingMem);
    g_setup.stagingAllocNs = nowNs() - e;
    e = nowNs();
    VKC(vkMapMemory(g_dev, g_stagingMem, 0, VK_WHOLE_SIZE, 0, &g_stagingPtr));
    g_setup.stagingMapNs = nowNs() - e;
    g_invRange = {VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE, nullptr, g_stagingMem, 0, VK_WHOLE_SIZE};

    // ---- device-local source buffer (buffer->buffer cells)
    e = nowNs();
    int tDev = findMemType(VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, 0);
    allocBuffer(IMG_BYTES, VK_BUFFER_USAGE_TRANSFER_SRC_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT,
                tDev, &g_srcBuf, &g_srcBufMem);
    // ---- images (image->buffer cells): real 1080p + 1x1 (4-byte cell)
    allocImage(IMG_W, IMG_H, tDev, &g_imgBig, &g_imgBigMem);
    allocImage(1, 1, tDev, &g_img1x1, &g_img1x1Mem);
    g_setup.srcAllocNs = nowNs() - e;

    // ---- upload staging (setup-only)
    int tHost = findMemType(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT, 0);
    if (tHost < 0) tHost = findMemType(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT, 0);
    allocBuffer(IMG_BYTES, VK_BUFFER_USAGE_TRANSFER_SRC_BIT, tHost, &g_fillStaging, &g_fillStagingMem);

    // ---- ordinary RAM destinations
    g_ramA.assign(IMG_BYTES, 0);
    g_ramB.assign(IMG_BYTES, 0);

    // ---- command pool / buffers / fences / query pool
    VkCommandPoolCreateInfo cpi{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
    cpi.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    cpi.queueFamilyIndex = g_famG;
    VKC(vkCreateCommandPool(g_dev, &cpi, nullptr, &g_cmdPool));
    VkCommandBufferAllocateInfo cbi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
    cbi.commandPool = g_cmdPool; cbi.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY; cbi.commandBufferCount = 1;
    VKC(vkAllocateCommandBuffers(g_dev, &cbi, &g_cmdMain));
    VKC(vkAllocateCommandBuffers(g_dev, &cbi, &g_cmdBacklog));
    VKC(vkAllocateCommandBuffers(g_dev, &cbi, &g_cmdWitness));
    VKC(vkAllocateCommandBuffers(g_dev, &cbi, &g_cmdTouch));
    VkFenceCreateInfo fci{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
    VKC(vkCreateFence(g_dev, &fci, nullptr, &g_fenceMain));
    VKC(vkCreateFence(g_dev, &fci, nullptr, &g_fenceBacklog));
    VKC(vkCreateFence(g_dev, &fci, nullptr, &g_fenceWitness));
    VKC(vkCreateFence(g_dev, &fci, nullptr, &g_fenceTouch));
    VkQueryPoolCreateInfo qpi{VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO};
    qpi.queryType = VK_QUERY_TYPE_TIMESTAMP;
    qpi.queryCount = 2;
    VKC(vkCreateQueryPool(g_dev, &qpi, nullptr, &g_queryPool));
}

// one-time fill of the sources: pattern-upload buffer->buffer, buffer->image,
// then park both images in TRANSFER_SRC_OPTIMAL forever.
static void fillSources() {
    uint8_t* fp = nullptr;
    VKC(vkMapMemory(g_dev, g_fillStagingMem, 0, VK_WHOLE_SIZE, 0, (void**)&fp));
    for (VkDeviceSize i = 0; i < IMG_BYTES; ++i) fp[i] = (uint8_t)(i * 7 + 3);
    vkUnmapMemory(g_dev, g_fillStagingMem);

    VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    VKC(vkBeginCommandBuffer(g_cmdTouch, &bi)); // reuse g_cmdTouch as the one-shot setup cmd
    VkBufferCopy bufFill{0, 0, IMG_BYTES};
    vkCmdCopyBuffer(g_cmdTouch, g_fillStaging, g_srcBuf, 1, &bufFill);

    const VkImageSubresourceRange colorAll{VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    VkImageMemoryBarrier imgToDst{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
    imgToDst.srcAccessMask = 0; imgToDst.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    imgToDst.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED; imgToDst.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    imgToDst.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    imgToDst.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    imgToDst.subresourceRange = colorAll;
    VkImageMemoryBarrier dstToSrc = imgToDst;
    dstToSrc.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    dstToSrc.dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;
    dstToSrc.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    dstToSrc.newLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;

    VkBufferImageCopy reg{};
    reg.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    reg.imageExtent = {IMG_W, IMG_H, 1};
    imgToDst.image = g_imgBig;
    vkCmdPipelineBarrier(g_cmdTouch,
        VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0,
        0, nullptr, 0, nullptr, 1, &imgToDst);
    vkCmdCopyBufferToImage(g_cmdTouch, g_fillStaging, g_imgBig,
        VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &reg);
    dstToSrc.image = g_imgBig;
    vkCmdPipelineBarrier(g_cmdTouch,
        VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0,
        0, nullptr, 0, nullptr, 1, &dstToSrc);
    // 1x1 image: same path, 1x1 copy from the pattern buffer
    imgToDst.image = g_img1x1;
    vkCmdPipelineBarrier(g_cmdTouch,
        VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0,
        0, nullptr, 0, nullptr, 1, &imgToDst);
    VkBufferImageCopy reg1{};
    reg1.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    reg1.imageExtent = {1, 1, 1};
    vkCmdCopyBufferToImage(g_cmdTouch, g_fillStaging, g_img1x1,
        VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &reg1);
    dstToSrc.image = g_img1x1;
    vkCmdPipelineBarrier(g_cmdTouch,
        VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0,
        0, nullptr, 0, nullptr, 1, &dstToSrc);
    VKC(vkEndCommandBuffer(g_cmdTouch));
    double e = nowNs();
    submitAndWait(g_q0, g_cmdTouch, g_fenceTouch);
    g_setup.fillSubmitNs = nowNs() - e;
}

// record the per-regime main command buffer (reused every iteration)
static void recordMain(VkCommandBuffer cmd, bool imageMode, VkDeviceSize bytes) {
    VKC(vkResetCommandBuffer(cmd, 0));
    VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    VKC(vkBeginCommandBuffer(cmd, &bi));
    vkCmdResetQueryPool(cmd, g_queryPool, 0, 2);
    vkCmdWriteTimestamp(cmd, VK_PIPELINE_STAGE_TRANSFER_BIT, g_queryPool, 0);
    if (imageMode) {
        VkImage img = (bytes == 4) ? g_img1x1 : g_imgBig;
        VkBufferImageCopy reg{};
        reg.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
        reg.imageExtent = (bytes == 4) ? VkExtent3D{1, 1, 1} : VkExtent3D{IMG_W, IMG_H, 1};
        vkCmdCopyImageToBuffer(cmd, img, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                               g_staging, 1, &reg);
    } else {
        VkBufferCopy bc{0, 0, bytes};
        vkCmdCopyBuffer(cmd, g_srcBuf, g_staging, 1, &bc);
    }
    vkCmdWriteTimestamp(cmd, VK_PIPELINE_STAGE_TRANSFER_BIT, g_queryPool, 1);
    VKC(vkEndCommandBuffer(cmd));
}

static void recordWitness() {
    VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    VKC(vkBeginCommandBuffer(g_cmdWitness, &bi));
    // tiny, fully resource-independent copy (64 KB from srcBuf tail into staging tail)
    VkBufferCopy bc{IMG_BYTES - 65536, IMG_BYTES - 65536, 65536};
    vkCmdCopyBuffer(g_cmdWitness, g_srcBuf, g_staging, 1, &bc);
    VKC(vkEndCommandBuffer(g_cmdWitness));
}

static bool createBacklog() {
    int tDev = findMemType(VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, 0);
    for (VkDeviceSize pair : { (VkDeviceSize)512ull << 20, (VkDeviceSize)256ull << 20 }) {
        g_backlog.clear();
        bool ok = true;
        for (int i = 0; i < 4 && ok; ++i) {
            BlkPair p{};
            allocBuffer(pair, VK_BUFFER_USAGE_TRANSFER_SRC_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT,
                        tDev, &p.a, &p.ma);
            allocBuffer(pair, VK_BUFFER_USAGE_TRANSFER_SRC_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT,
                        tDev, &p.b, &p.mb);
            g_backlog.push_back(p);
        }
        if (ok) { g_backlogPairBytes = pair; return true; }
        for (auto& p : g_backlog) {
            vkDestroyBuffer(g_dev, p.a, nullptr); vkDestroyBuffer(g_dev, p.b, nullptr);
            vkFreeMemory(g_dev, p.ma, nullptr); vkFreeMemory(g_dev, p.mb, nullptr);
        }
    }
    return false;
}

static void recordBacklog() {
    VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    VKC(vkBeginCommandBuffer(g_cmdBacklog, &bi));
    for (auto& p : g_backlog) {
        VkBufferCopy bc{0, 0, g_backlogPairBytes};
        vkCmdCopyBuffer(g_cmdBacklog, p.a, p.b, 1, &bc);
    }
    VKC(vkEndCommandBuffer(g_cmdBacklog));
}

// ------------------------------------------------------------- regimes ----
struct Regime {
    const char* name;
    bool imageMode;
    VkDeviceSize bytes;
    bool noRead;
    bool backlog;
    bool witness;
    double idleSleepSec;
    int warmIters;
    bool noFence;   // engine-shape probe: submit copy, DO NOT wait the fence,
                    // go straight to the mapped read — shows where the wait
                    // lands when the copy->host-visibility dependency is omitted
};

static FILE* g_csv;
static std::vector<Regime> g_regimes;
static std::vector<std::vector<Iter>> g_iters;

static void csvRow(const Regime& r, const Iter& it) {
    fprintf(g_csv, "%s,%d,%d", r.name, it.idx, (int)it.cold);
    for (int i = 0; i < T_COUNT; ++i) fprintf(g_csv, ",%.0f", it.t[i]);
    fprintf(g_csv, ",%.0f,%.0f,%d,%d\n", it.gpu0ns, it.gpu1ns,
            (int)it.wAlreadyDone, (int)it.wSaw);
}

static void runRegime(const Regime& r) {
    recordMain(g_cmdMain, r.imageMode, r.bytes);
    std::vector<Iter> out;
    out.reserve(r.warmIters);

    for (int i = 0; i < r.warmIters; ++i) {
        if (r.idleSleepSec > 0 && i > 0) Sleep((DWORD)(r.idleSleepSec * 1000.0));
        Iter it{};
        it.idx = i;
        it.cold = (i == 0);
        memset(it.t, 0, sizeof(it.t));

        if (r.backlog) {
            vkResetFences(g_dev, 1, &g_fenceBacklog);
            it.t[T_BSUB_ENTRY] = nowNs();
            VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
            si.commandBufferCount = 1; si.pCommandBuffers = &g_cmdBacklog;
            VKC(vkQueueSubmit(g_q0, 1, &si, g_fenceBacklog));
            it.t[T_BSUB_RETURN] = nowNs();
        }
        vkResetFences(g_dev, 1, &g_fenceMain);
        if (r.witness) vkResetFences(g_dev, 1, &g_fenceWitness);

        it.t[T_REQUEST] = nowNs();
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        si.commandBufferCount = 1; si.pCommandBuffers = &g_cmdMain;
        it.t[T_SUBMIT_ENTRY] = nowNs();
        VKC(vkQueueSubmit(g_q0, 1, &si, g_fenceMain));
        it.t[T_SUBMIT_RETURN] = nowNs();

        if (r.witness) {
            // independent job on a SECOND queue, submitted right after the
            // readback request — does it also stop when the readback stalls?
            VkSubmitInfo wi{VK_STRUCTURE_TYPE_SUBMIT_INFO};
            wi.commandBufferCount = 1; wi.pCommandBuffers = &g_cmdWitness;
            it.t[T_WSUB_ENTRY] = nowNs();
            VKC(vkQueueSubmit(g_q1, 1, &wi, g_fenceWitness));
            it.t[T_WSUB_RETURN] = nowNs();
        }

        it.t[T_FWAIT_ENTRY] = nowNs();
        if (r.noFence) {
            // engine-shape: no wait at all — the dependency is (wrongly)
            // assumed established by the mapping itself
            it.t[T_FWAIT_ENTRY] = it.t[T_SUBMIT_RETURN];
            it.t[T_FWAIT_RETURN] = it.t[T_SUBMIT_RETURN];
        } else if (r.witness) {
            // polled wait: observe BOTH fences on one continuous timeline
            bool a = false, b = false;
            for (;;) {
                VkResult ra = vkWaitForFences(g_dev, 1, &g_fenceMain, VK_FALSE, 500000 /*0.5ms*/);
                double tn = nowNs();
                if (!a && ra == VK_SUCCESS) { a = true; it.t[T_FWAIT_RETURN] = tn; }
                if (!b && vkGetFenceStatus(g_dev, g_fenceWitness) == VK_SUCCESS) {
                    b = true; it.t[T_WSIG] = tn;
                    it.wAlreadyDone = !a; // witness done while readback still pending
                }
                if (a && b) break;
            }
            it.wSaw = true;
        } else {
            VKC(vkWaitForFences(g_dev, 1, &g_fenceMain, VK_TRUE, UINT64_MAX));
            it.t[T_FWAIT_RETURN] = nowNs();
        }

        if (!r.noRead) {
            // Astra step order: invalidate (if noncoherent) -> first read ->
            // bulk memcpy into ordinary RAM -> RAM-only swizzle -> consumer
            if (!g_setup.coherent) {
                it.t[T_INV_ENTRY] = nowNs();
                VKC(vkInvalidateMappedMemoryRanges(g_dev, 1, &g_invRange));
                it.t[T_INV_RETURN] = nowNs();
            } else {
                it.t[T_INV_ENTRY] = it.t[T_FWAIT_RETURN];
                it.t[T_INV_RETURN] = it.t[T_FWAIT_RETURN];
            }
            volatile uint8_t* m = (volatile uint8_t*)g_stagingPtr;
            it.t[T_FIRST_READ] = nowNs();
            g_sink += m[0]; // first CPU read of mapped memory
            it.t[T_FIRST_READ] = nowNs();
            memcpy(g_ramA.data(), g_stagingPtr, (size_t)r.bytes);
            it.t[T_MEMCPY_DONE] = nowNs();
            // BGRA<->RGBA swizzle in ordinary RAM
            const uint8_t* s = g_ramA.data();
            uint8_t* d = g_ramB.data();
            for (VkDeviceSize o = 0; o < r.bytes; o += 4) {
                d[o + 0] = s[o + 2]; d[o + 1] = s[o + 1];
                d[o + 2] = s[o + 0]; d[o + 3] = s[o + 3];
            }
            it.t[T_SWIZZLE_DONE] = nowNs();
            uint64_t h = 1469598103934665603ull;
            for (VkDeviceSize o = 0; o < r.bytes; ++o) h = (h ^ d[o]) * 1099511628211ull;
            g_sink += h;
            it.t[T_CONSUMER] = nowNs();
        } else {
            // row 3: copy + completion, NO CPU data access at all
            it.t[T_INV_ENTRY] = it.t[T_FWAIT_RETURN];
            it.t[T_INV_RETURN] = it.t[T_FWAIT_RETURN];
            it.t[T_FIRST_READ] = it.t[T_FWAIT_RETURN];
            it.t[T_MEMCPY_DONE] = it.t[T_FWAIT_RETURN];
            it.t[T_SWIZZLE_DONE] = it.t[T_FWAIT_RETURN];
            it.t[T_CONSUMER] = it.t[T_FWAIT_RETURN];
        }

        uint64_t ts[2] = {0, 0};
        if (r.noFence) {
            // drain AFTER the timeline segments: how long the NEXT submission
            // would inherit (residual GPU work). Landed on T_GPU_RET.
            while (vkGetFenceStatus(g_dev, g_fenceMain) != VK_SUCCESS) {}
        }
        VKC(vkGetQueryPoolResults(g_dev, g_queryPool, 0, 2, sizeof(ts), ts,
                                  sizeof(uint64_t), VK_QUERY_RESULT_64_BIT));
        it.t[T_GPU_RET] = nowNs();
        it.gpu0ns = (double)ts[0] * g_tsPeriodNs;
        it.gpu1ns = (double)ts[1] * g_tsPeriodNs;

        out.push_back(it);
        csvRow(r, it);
    }
    g_iters.push_back(std::move(out));
}

// ----------------------------------------------- residency-pressure row ---
static bool createPressure(size_t wantGB) {
    int tDev = findMemType(VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, 0);
    uint32_t heapIdx = g_memprops.memoryTypes[tDev].heapIndex;
    VkDeviceSize heapSize = g_memprops.memoryHeaps[heapIdx].size;
    VkDeviceSize budget = heapSize - (VkDeviceSize)(1.5 * (double)(1ull << 30));
    VkDeviceSize chunk = (VkDeviceSize)1 << 30;
    size_t maxChunks = (size_t)(budget / chunk);
    const size_t AUTO_CAP = 20; // never auto-commit more than 20 GB
    size_t chunks = std::min(wantGB ? wantGB : AUTO_CAP, maxChunks);
    if (chunks == 0) return false;
    for (size_t i = 0; i < chunks; ++i) {
        PressChunk c{};
        VkBufferCreateInfo bi{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
        bi.size = chunk; bi.usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT;
        VkResult ra = vkCreateBuffer(g_dev, &bi, nullptr, &c.b);
        if (ra != VK_SUCCESS) break;
        VkMemoryRequirements mr;
        vkGetBufferMemoryRequirements(g_dev, c.b, &mr);
        ra = vkAllocateMemory(g_dev, &(VkMemoryAllocateInfo{
            VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, nullptr, mr.size, (uint32_t)tDev}),
            nullptr, &c.m);
        if (ra != VK_SUCCESS) { vkDestroyBuffer(g_dev, c.b, nullptr); break; }
        vkBindBufferMemory(g_dev, c.b, c.m, 0);
        g_press.push_back(c);
        g_pressTotal += chunk;
    }
    return !g_press.empty();
}

static void recordTouch() {
    VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    VKC(vkBeginCommandBuffer(g_cmdTouch, &bi));
    for (auto& c : g_press) vkCmdFillBuffer(g_cmdTouch, c.b, 0, VK_WHOLE_SIZE, 0x3F3F3F3F);
    VKC(vkEndCommandBuffer(g_cmdTouch));
}

// ------------------------------------------------------------- analysis ---
struct Seg { const char* name; int a, b; bool isGpu; };
static const Seg SEGS[] = {
    {"pre_submit",       T_REQUEST, T_SUBMIT_ENTRY, false},
    {"submit",           T_SUBMIT_ENTRY, T_SUBMIT_RETURN, false},
    {"fence_wait",       T_FWAIT_ENTRY, T_FWAIT_RETURN, false},
    {"invalidate",       T_INV_ENTRY, T_INV_RETURN, false},
    {"first_read",       T_FWAIT_RETURN, T_FIRST_READ, false},
    {"bulk_memcpy",      T_FIRST_READ, T_MEMCPY_DONE, false},
    {"ram_swizzle",      T_MEMCPY_DONE, T_SWIZZLE_DONE, false},
    {"consumer",         T_SWIZZLE_DONE, T_CONSUMER, false},
    {"gpu_copy",         0, 1, true},
};

static double median(std::vector<double> v) {
    if (v.empty()) return 0;
    std::sort(v.begin(), v.end());
    size_t n = v.size();
    return n % 2 ? v[n / 2] : 0.5 * (v[n / 2 - 1] + v[n / 2]);
}

static double g_teardownNs = 0;

static void writeSummary(const char* outDir) {
    char p[512];
    snprintf(p, sizeof(p), "%s/summary.md", outDir);
    FILE* f = fopen(p, "w");
    if (!f) return;
    fprintf(f, "# A4 readback_probe — results\n\n");
    fprintf(f, "Adapter: %s (driver %u) · api %u.%u.%u · timestampPeriod %.3f ns · ReBAR: %s\n\n",
            g_pdprops.deviceName, g_pdprops.driverVersion,
            VK_API_VERSION_MAJOR(g_pdprops.apiVersion), VK_API_VERSION_MINOR(g_pdprops.apiVersion),
            VK_API_VERSION_PATCH(g_pdprops.apiVersion), g_tsPeriodNs, g_hasReBAR ? "yes" : "no");
    fprintf(f, "Staging: memory type %d (%s%s%s), alloc %.1f us, map %.1f us · one-time source fill+submit %.3f ms · teardown %.3f ms\n\n",
            g_setup.stagingType,
            (g_memprops.memoryTypes[g_setup.stagingType].propertyFlags & VK_MEMORY_PROPERTY_HOST_CACHED_BIT) ? "HOST_CACHED " : "",
            g_setup.coherent ? "HOST_COHERENT" : "NON-COHERENT",
            g_hasReBAR ? " (device-local heap visible? see types)" : "",
            g_setup.stagingAllocNs / 1e3, g_setup.stagingMapNs / 1e3,
            g_setup.fillSubmitNs / 1e6, g_teardownNs / 1e6);
    fprintf(f, "All numbers are ns unless suffixed. median/max over warm iterations (cold row listed separately). Segments are consecutive differences of the ONE continuous timeline.\n\n");

    for (size_t ri = 0; ri < g_regimes.size(); ++ri) {
        const Regime& r = g_regimes[ri];
        const std::vector<Iter>& it = g_iters[ri];
        fprintf(f, "## %s\n\n", r.name);
        // cold rows
        for (auto& x : it) if (x.cold) {
            double e2e = x.t[T_CONSUMER] - x.t[T_REQUEST];
            double fw = x.t[T_FWAIT_RETURN] - x.t[T_FWAIT_ENTRY];
            fprintf(f, "- COLD iter0: e2e %.0f ns (%.3f ms), fence_wait %.0f ns, gpu_copy %.0f ns",
                    e2e, e2e / 1e6, fw, x.gpu1ns - x.gpu0ns);
            if (x.t[T_WSIG] > 0)
                fprintf(f, ", witness_sig - fwait_return = %.0f ns (neg = witness done BEFORE readback)",
                        x.t[T_WSIG] - x.t[T_FWAIT_RETURN]);
            fprintf(f, "\n");
        }
        // warm stats
        std::vector<double> segMed(sizeof(SEGS) / sizeof(SEGS[0]));
        std::vector<double> segMax(sizeof(SEGS) / sizeof(SEGS[0]));
        for (size_t s = 0; s < sizeof(SEGS) / sizeof(SEGS[0]); ++s) {
            std::vector<double> vals, mx;
            for (size_t i = 1; i < it.size(); ++i) {
                double v = SEGS[s].isGpu ? (it[i].gpu1ns - it[i].gpu0ns)
                                         : (it[i].t[SEGS[s].b] - it[i].t[SEGS[s].a]);
                if (v < 0) v = 0;
                vals.push_back(v);
            }
            segMed[s] = median(vals);
            segMax[s] = vals.empty() ? 0 : *std::max_element(vals.begin(), vals.end());
        }
        std::vector<double> e2e, fwait, e2eRead;
        for (size_t i = 1; i < it.size(); ++i) {
            e2e.push_back(it[i].t[T_CONSUMER] - it[i].t[T_REQUEST]);
            fwait.push_back(it[i].t[T_FWAIT_RETURN] - it[i].t[T_FWAIT_ENTRY]);
            e2eRead.push_back(it[i].t[T_SWIZZLE_DONE] - it[i].t[T_REQUEST]);
        }
        fprintf(f, "\n| segment | median ns | max ns |\n|---|---:|---:|\n");
        for (size_t s = 0; s < sizeof(SEGS) / sizeof(SEGS[0]); ++s)
            fprintf(f, "| %s | %.0f | %.0f |\n", SEGS[s].name, segMed[s], segMax[s]);
        fprintf(f, "| **e2e_read (request->swizzle_done)** | %.0f | %.0f |\n", median(e2eRead), e2eRead.empty() ? 0 : *std::max_element(e2eRead.begin(), e2eRead.end()));
        fprintf(f, "| e2e (request->consumer; incl. hash) | %.0f | %.0f |\n", median(e2e), e2e.empty() ? 0 : *std::max_element(e2e.begin(), e2e.end()));
        if (!r.noRead) {
            double thr = (double)r.bytes / (median(e2e) / 1e9) / 1e6;
            fprintf(f, "| effective throughput (median e2e) | %.1f MB/s | | \n", thr);
        }
        if (r.witness) {
            std::vector<double> wdelta, wpre;
            for (size_t i = 1; i < it.size(); ++i) {
                wdelta.push_back(it[i].t[T_WSIG] - it[i].t[T_FWAIT_RETURN]);
                if (it[i].wAlreadyDone) wpre.push_back(1);
            }
            fprintf(f, "\nWITNESS: median(witness_sig - fwait_return) = %.0f ns (negative => independent work completed BEFORE the readback did); witness already done at first poll in %zu/%zu warm iters.\n",
                    median(wdelta), wpre.size(), wdelta.size());
        }
        fprintf(f, "\n");
    }
    fclose(f);
}

int main(int argc, char** argv) {
    timeInit();
    SetPriorityClass(GetCurrentProcess(), HIGH_PRIORITY_CLASS);

    size_t pressureGB = 0;
    bool doPressure = true;
    char outDir[400] = "results";
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--pressure") && i + 1 < argc) pressureGB = (size_t)atoi(argv[++i]);
        else if (!strcmp(argv[i], "--nopressure")) doPressure = false;
        else if (!strcmp(argv[i], "--out") && i + 1 < argc) snprintf(outDir, sizeof(outDir), "%s", argv[++i]);
    }
    CreateDirectoryA(outDir, nullptr);
    char csvPath[512];
    snprintf(csvPath, sizeof(csvPath), "%s/raw_timeline.csv", outDir);
    g_csv = fopen(csvPath, "w");
    if (!g_csv) { fprintf(stderr, "cannot open %s\n", csvPath); return 3; }
    fprintf(g_csv, "regime,iter,cold");
    for (int i = 0; i < T_COUNT; ++i) fprintf(g_csv, ",%s", TNAME[i]);
    fprintf(g_csv, ",gpu_ts0_ns,gpu_ts1_ns,witness_already_done,witness_observed\n");

    initVulkan();
    printf("adapter: %s  driverver=%u  tsPeriod=%.3f ns  ReBAR=%s\n",
           g_pdprops.deviceName, g_pdprops.driverVersion, g_tsPeriodNs, g_hasReBAR ? "yes" : "no");
    printf("memory types:\n");
    for (uint32_t i = 0; i < g_memprops.memoryTypeCount; ++i) {
        uint32_t heap = g_memprops.memoryTypes[i].heapIndex;
        printf("  type %u: props=0x%x heap %u (%.1f GB %s%s)\n", i,
               g_memprops.memoryTypes[i].propertyFlags, heap,
               g_memprops.memoryHeaps[heap].size / 1073741824.0,
               (g_memprops.memoryHeaps[heap].flags & VK_MEMORY_HEAP_DEVICE_LOCAL_BIT) ? "DEVLOCAL" : "host",
               (g_memprops.memoryTypes[i].propertyFlags & VK_MEMORY_PROPERTY_HOST_COHERENT_BIT) ? " coherent" : "");
    }

    createResources();
    fillSources();
    printf("staging: type %d %s, alloc %.1f us, map %.1f us; one-time fill %.3f ms\n",
           g_setup.stagingType, g_setup.coherent ? "HOST_COHERENT (invalidate is a no-op)" : "NON-COHERENT (invalidate is in the chain)",
           g_setup.stagingAllocNs / 1e3, g_setup.stagingMapNs / 1e3, g_setup.fillSubmitNs / 1e6);

    // ---------------- the matrix (Astra rows 1-5) ----------------
    auto add = [&](const char* n, bool img, VkDeviceSize b, bool nr, bool bl, bool wit, double sl, int it) {
        g_regimes.push_back({n, img, b, nr, bl, wit, sl, it});
    };
    // idle cells (first regime's iter0 = the process "boot pull" analog)
    add("img8M_full_idle",    true,  IMG_BYTES, false, false, false, 0,   40);
    add("img4B_full_idle",    true,  4,         false, false, false, 0,   40);
    add("buf8M_full_idle",    false, IMG_BYTES, false, false, false, 0,   40);
    add("buf4B_full_idle",    false, 4,         false, false, false, 0,   40);
    add("img8M_noread_idle",  true,  IMG_BYTES, true,  false, false, 0,   40);
    add("img4B_noread_idle",  true,  4,         true,  false, false, 0,   40);
    add("buf8M_noread_idle",  false, IMG_BYTES, true,  false, false, 0,   40);
    add("buf4B_noread_idle",  false, 4,         true,  false, false, 0,   40);
    // backlog cells (row 5) — created after the idle cells so those stay pure
    bool haveBacklog = createBacklog();
    if (haveBacklog) { recordBacklog(); printf("backlog: 4 pairs x %.0f MB device-local\n", g_backlogPairBytes / 1048576.0); }
    if (haveBacklog) {
        add("img8M_full_backlog",    true,  IMG_BYTES, false, true, false, 0, 40);
        add("img8M_noread_backlog",  true,  IMG_BYTES, true,  true, false, 0, 40);
        add("buf8M_full_backlog",    false, IMG_BYTES, false, true, false, 0, 40);
        add("buf8M_noread_backlog",  false, IMG_BYTES, true,  true, false, 0, 40);
        add("img4B_full_backlog",    true,  4,         false, true, false, 0, 40);
        add("img4B_noread_backlog",  true,  4,         true,  true, false, 0, 40);
        add("buf4B_full_backlog",    false, 4,         false, true, false, 0, 40);
        add("buf4B_noread_backlog",  false, 4,         true,  true, false, 0, 40);
    } else {
        printf("WARNING: backlog buffers could not be allocated; row 5 backlog cells skipped\n");
    }
    // decisive-signature probes
    recordWitness();
    add("img8M_full_witness",    true,  IMG_BYTES, false, false, true,  0,   20);
    add("img8M_full_idlesleep",  true,  IMG_BYTES, false, false, false, 3.0, 10);
    // engine-shape probes: omitted fence dependency (wait lands at first touch)
    g_regimes.push_back({"img8M_full_nofence_idle", true, IMG_BYTES, false, false, false, 0, 40, true});
    if (haveBacklog)
        g_regimes.push_back({"img8M_full_nofence_backlog", true, IMG_BYTES, false, true, false, 0, 40, true});

    for (auto& r : g_regimes) {
        printf("running %s ...\n", r.name);
        runRegime(r);
    }

    // residency-pressure run (paging signature): fill most of VRAM with
    // resident buffers, re-touch every iteration, then readback.
    if (doPressure) {
        size_t want = pressureGB;
        if (createPressure(want)) {
            recordTouch();
            printf("pressure: %zu chunks, %.1f GB committed device-local\n",
                   g_press.size(), g_pressTotal / 1073741824.0);
            // pin once with a waited submit
            double e = nowNs();
            vkResetFences(g_dev, 1, &g_fenceTouch);
            submitAndWait(g_q0, g_cmdTouch, g_fenceTouch);
            printf("pressure pin pass: %.2f ms\n", (nowNs() - e) / 1e6);
            Regime pr{"img8M_full_pressure", true, IMG_BYTES, false, false, false, 0, 40};
            recordMain(g_cmdMain, pr.imageMode, pr.bytes);
            // churn variant: re-touch (fill) every iteration before the readback
            std::vector<Iter> out;
            for (int i = 0; i < pr.warmIters; ++i) {
                Iter it{};
                it.idx = i; it.cold = (i == 0);
                memset(it.t, 0, sizeof(it.t));
                vkResetFences(g_dev, 1, &g_fenceTouch);
                it.t[T_BSUB_ENTRY] = nowNs();
                VkSubmitInfo ti{VK_STRUCTURE_TYPE_SUBMIT_INFO};
                ti.commandBufferCount = 1; ti.pCommandBuffers = &g_cmdTouch;
                VKC(vkQueueSubmit(g_q0, 1, &ti, g_fenceTouch));
                it.t[T_BSUB_RETURN] = nowNs();
                vkResetFences(g_dev, 1, &g_fenceMain);
                it.t[T_REQUEST] = nowNs();
                VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
                si.commandBufferCount = 1; si.pCommandBuffers = &g_cmdMain;
                it.t[T_SUBMIT_ENTRY] = nowNs();
                VKC(vkQueueSubmit(g_q0, 1, &si, g_fenceMain));
                it.t[T_SUBMIT_RETURN] = nowNs();
                it.t[T_FWAIT_ENTRY] = nowNs();
                VKC(vkWaitForFences(g_dev, 1, &g_fenceMain, VK_TRUE, UINT64_MAX));
                it.t[T_FWAIT_RETURN] = nowNs();
                if (!g_setup.coherent) {
                    it.t[T_INV_ENTRY] = nowNs();
                    VKC(vkInvalidateMappedMemoryRanges(g_dev, 1, &g_invRange));
                    it.t[T_INV_RETURN] = nowNs();
                } else {
                    it.t[T_INV_ENTRY] = it.t[T_FWAIT_RETURN];
                    it.t[T_INV_RETURN] = it.t[T_FWAIT_RETURN];
                }
                it.t[T_FIRST_READ] = nowNs();
                g_sink += ((volatile uint8_t*)g_stagingPtr)[0];
                it.t[T_FIRST_READ] = nowNs();
                memcpy(g_ramA.data(), g_stagingPtr, (size_t)IMG_BYTES);
                it.t[T_MEMCPY_DONE] = nowNs();
                const uint8_t* s = g_ramA.data(); uint8_t* d = g_ramB.data();
                for (VkDeviceSize o = 0; o < IMG_BYTES; o += 4) {
                    d[o + 0] = s[o + 2]; d[o + 1] = s[o + 1];
                    d[o + 2] = s[o + 0]; d[o + 3] = s[o + 3];
                }
                it.t[T_SWIZZLE_DONE] = nowNs();
                uint64_t h = 1469598103934665603ull;
                for (VkDeviceSize o = 0; o < IMG_BYTES; ++o) h = (h ^ d[o]) * 1099511628211ull;
                g_sink += h;
                it.t[T_CONSUMER] = nowNs();
                uint64_t ts[2] = {0, 0};
                VKC(vkGetQueryPoolResults(g_dev, g_queryPool, 0, 2, sizeof(ts), ts,
                                          sizeof(uint64_t), VK_QUERY_RESULT_64_BIT));
                it.t[T_GPU_RET] = nowNs();
                it.gpu0ns = (double)ts[0] * g_tsPeriodNs;
                it.gpu1ns = (double)ts[1] * g_tsPeriodNs;
                out.push_back(it);
                csvRow(pr, it);
            }
            g_regimes.push_back(pr);
            g_iters.push_back(std::move(out));
        } else {
            printf("pressure: allocation failed, skipped\n");
        }
    }

    double te = nowNs();
    VKC(vkDeviceWaitIdle(g_dev));
    for (auto& c : g_press) { vkDestroyBuffer(g_dev, c.b, nullptr); vkFreeMemory(g_dev, c.m, nullptr); }
    for (auto& p : g_backlog) {
        vkDestroyBuffer(g_dev, p.a, nullptr); vkDestroyBuffer(g_dev, p.b, nullptr);
        vkFreeMemory(g_dev, p.ma, nullptr); vkFreeMemory(g_dev, p.mb, nullptr);
    }
    vkDestroyQueryPool(g_dev, g_queryPool, nullptr);
    vkDestroyFence(g_dev, g_fenceMain, nullptr);
    vkDestroyFence(g_dev, g_fenceBacklog, nullptr);
    vkDestroyFence(g_dev, g_fenceWitness, nullptr);
    vkDestroyFence(g_dev, g_fenceTouch, nullptr);
    vkDestroyCommandPool(g_dev, g_cmdPool, nullptr);
    vkUnmapMemory(g_dev, g_stagingMem);
    vkDestroyBuffer(g_dev, g_staging, nullptr);   vkFreeMemory(g_dev, g_stagingMem, nullptr);
    vkDestroyBuffer(g_dev, g_srcBuf, nullptr);    vkFreeMemory(g_dev, g_srcBufMem, nullptr);
    vkDestroyBuffer(g_dev, g_fillStaging, nullptr); vkFreeMemory(g_dev, g_fillStagingMem, nullptr);
    vkDestroyImage(g_dev, g_imgBig, nullptr);     vkFreeMemory(g_dev, g_imgBigMem, nullptr);
    vkDestroyImage(g_dev, g_img1x1, nullptr);     vkFreeMemory(g_dev, g_img1x1Mem, nullptr);
    vkDestroyDevice(g_dev, nullptr);
    vkDestroyInstance(g_inst, nullptr);
    g_teardownNs = nowNs() - te;

    fclose(g_csv);
    writeSummary(outDir);
    printf("done. sink=%llu  csv=%s  summary=%s/summary.md\n",
           (unsigned long long)g_sink, csvPath, outDir);
    return 0;
}
