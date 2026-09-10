struct ShutdownCancellation {};
static std::atomic<bool> g_shutdown_closing{false};
#ifdef CHIMERA_SHUTDOWN_TEST
static std::atomic<bool> g_shutdown_test_boot_waiting{false};
#endif

template <class Condition, class Lock, class Rep, class Period, class Predicate>
static bool wait_for_shutdown(Condition& cv, Lock& lock,
                              const std::chrono::duration<Rep, Period>& timeout,
                              Predicate predicate) {
#ifdef CHIMERA_SHUTDOWN_TEST
    printf("shutdown_test: wait_entered\n");
    fflush(stdout);
#endif
    cv.wait_for(lock, timeout, [&] {
        return predicate() || g_shutdown_closing.load(std::memory_order_acquire);
    });
    // The render thread owns the applied flag under this same channel mutex.
    // Recheck it while still holding the caller's lock so cancellation cannot
    // turn an already-applied request into a false cancellation.
    if (g_shutdown_closing.load(std::memory_order_acquire) && !predicate())
        throw ShutdownCancellation{};
    return predicate();
}

template <class Mutex, class Condition>
static void notify_shutdown(Mutex& mutex, Condition& cv) {
    // mutant omits notification lock
    cv.notify_all();
}

static bool wait_for_shutdown_delay(std::mutex& mutex, std::condition_variable& cv,
                                    const std::atomic<bool>& cancel,
                                    std::chrono::milliseconds delay) {
    std::unique_lock<std::mutex> lock(mutex);
#ifdef CHIMERA_SHUTDOWN_TEST
    g_shutdown_test_boot_waiting.store(true, std::memory_order_release);
    printf("shutdown_test: boot_wait_entered\n");
    fflush(stdout);
#endif
    return cv.wait_for(lock, delay, [&] {
        return cancel.load(std::memory_order_acquire)
            || g_shutdown_closing.load(std::memory_order_acquire);
    });
}

static void notify_shutdown_channels() {
    notify_shutdown(g_mem_mutex, g_mem_cv);
    notify_shutdown(g_md_mutex, g_md_cv);
    notify_shutdown(g_mesh_mutex, g_mesh_cv);
    notify_shutdown(g_hinge_mutex, g_hinge_cv);
    notify_shutdown(g_water_mutex, g_water_cv);
    notify_shutdown(g_gait_mutex, g_gait_cv);
    notify_shutdown(g_volp_mutex, g_volp_cv);
    notify_shutdown(g_frost_mutex, g_frost_cv);
    notify_shutdown(g_skin_mutex, g_skin_cv);
}

