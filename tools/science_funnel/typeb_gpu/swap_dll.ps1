try {
    Copy-Item walker_env_co8.dll walker_env.dll -Force -ErrorAction Stop
    "SWAP_OK"
} catch {
    "LOCKED"
}
