#pragma once
// P05-R1 — Windows-only test seam for the Win32 surface backend.
//
// Lets the standalone harness substitute the loader's vkCreateWin32SurfaceKHR
// with a program-selected function carrying the REAL PFN_vkCreateWin32SurfaceKHR
// signature, so exact VkResult propagation can be probed on a CONTROLLED
// failure without violating Vulkan usage requirements (P05-P1 review point 5).
//
// Default (nullptr) keeps the production path: the backend calls the loaded
// vkCreateWin32SurfaceKHR directly and this seam is inert. The production
// engine never calls the setter. Single writer, single thread = harness only.
//
// This header is Windows-only and SELF-CONTAINED (it pulls <windows.h> so
// VkWin32SurfaceCreateInfoKHR's HWND/HINSTANCE members resolve); call sites
// must still include it only under _WIN32.

#include <windows.h>
#include <vulkan/vulkan.h>
#include <vulkan/vulkan_win32.h>

namespace plat {

// Replaces the Win32 creation call for subsequent plat::create_surface calls.
// Pass nullptr to restore the real loader path.
void win32_set_create_surface_override(PFN_vkCreateWin32SurfaceKHR fn) noexcept;

} // namespace plat