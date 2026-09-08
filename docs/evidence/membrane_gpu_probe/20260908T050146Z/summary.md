# Linux dependency installation blocker

This is an access-blocker record for `LUNA-LINUX-02`, not a membrane
verification result.

- **Source:** `9472ee331c8be4700ec65b9a05b694b904348b2d`
- **Install state:** `BLOCKED`
- **Reason:** WSL sudo requires a password unavailable to the agent.
- **System changes:** none.
- **Vulkan device observed:** `llvmpipe (LLVM 20.1.2, 256 bits)`, software
  Vulkan, API 1.4.318.
- **Verification:** CPU, build, GPU, and engine-window stages are all
  `NOT_TESTED`; no Linux PASS is claimed.

Required authorized setup inside Ubuntu WSL:

```bash
sudo apt-get update
sudo apt-get install -y cmake libvulkan-dev glslc python3-venv
cd /mnt/c/Users/allen/AppData/Local/Temp/opencode/chimera_pub
python3 -m venv .venv-linux
.venv-linux/bin/python -m pip install --disable-pip-version-check --no-input numpy
```

Raw command and result: `install_attempt.txt`; machine-readable state:
`result.json`.
