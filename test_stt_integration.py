#!/usr/bin/env python3
"""Test script for STT integration with whisper.cpp and VoiceEntity."""

import subprocess
import os
from pathlib import Path


def test_whisper_cli():
    """Test whisper.cpp CLI tool with a sample audio file."""

    # Create a simple WAV file for testing (1 second of silence at 16kHz)
    wav_path = "E:/PythonChimera/Chimera/test_audio.wav"
    print(f"Creating test WAV file: {wav_path}")

    # Use Python to create a simple WAV file
    import wave
    import struct

    sample_rate = 16000
    duration = 1.0  # seconds
    samples = int(sample_rate * duration)

    with wave.open(wav_path, "wb") as wav_file:
        wav_file.setnchannels(1)  # mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Write silence (zeros)
        for _ in range(samples):
            wav_file.writeframes(struct.pack("h", 0))

    print(f"Created {wav_path} ({duration}s, {sample_rate}Hz)")

    # Test whisper.cpp CLI
    whisper_cli = "E:/PythonChimera/Chimera/Source/ThirdParty/whisper.cpp/whisper-src/build/bin/Release/whisper-cli.exe"
    model_file = "E:/PythonChimera/Chimera/Content/AIModels/ggml-base.en.bin"

    print(f"\nTesting whisper.cpp CLI...")
    print(f"  Model: {model_file}")
    print(f"  Audio: {wav_path}")

    if not os.path.exists(model_file):
        print(f"ERROR: Model file not found at {model_file}")
        return False

    cmd = [whisper_cli, "-m", model_file, "-f", wav_path, "--output-txt"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        print(f"\nwhisper.cpp output:")
        print(f"  stdout: {result.stdout}")
        print(f"  stderr: {result.stderr[:200]}...")
        print(f"  return code: {result.returncode}")

        if result.returncode == 0:
            print("\nPASSED: whisper.cpp CLI test succeeded")
            return True
        else:
            print("\nFAILED: whisper.cpp CLI test failed")
            return False

    except Exception as e:
        print(f"\nFAIL whisper.cpp CLI test error: {e}")
        return False


def test_ue5_integration():
    """Test UE5 integration with whisper.cpp wrapper."""

    print("\nTesting UE5 C++ integration...")
    print("  This requires building the Chimera project with UBT.")
    print("  Run 'python run_deep_space_trader_pipeline.py' to build and test.")

    # Check if files exist
    whisper_wrapper_h = (
        "E:/PythonChimera/Chimera/Source/ThirdParty/whisper.cpp/WhisperWrapper.h"
    )
    whisper_wrapper_cpp = (
        "E:/PythonChimera/Chimera/Source/ThirdParty/whisper.cpp/WhisperWrapper.cpp"
    )

    if os.path.exists(whisper_wrapper_h) and os.path.exists(whisper_wrapper_cpp):
        print("  OK WhisperWrapper.h and WhisperWrapper.cpp exist")

        # Check if SttEngine.h exists
        stt_engine_h = "E:/PythonChimera/Chimera/Source/Chimera/AI/SttEngine.h"
        if os.path.exists(stt_engine_h):
            print("  OK SttEngine.h exists")

            # Check if Build.cs was updated
            build_cs = "E:/PythonChimera/Chimera/Source/Chimera/Chimera.Build.cs"
            with open(build_cs, "r") as f:
                content = f.read()
                if "whisper.cpp" in content.lower():
                    print("  OK Build.cs includes whisper.cpp paths")
                    return True
                else:
                    print("  FAIL Build.cs does not include whisper.cpp paths")
                    return False
        else:
            print("  FAIL SttEngine.h not found")
            return False
    else:
        print("  FAIL WhisperWrapper files not found")
        return False


def main():
    """Run all tests."""

    print("=" * 60)
    print("STT Integration Test Suite")
    print("=" * 60)

    # Test whisper.cpp CLI
    cli_passed = test_whisper_cli()

    # Test UE5 integration (just check files, don't build)
    ue5_ready = test_ue5_integration()

    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  whisper.cpp CLI: {'OK PASSED' if cli_passed else 'FAIL FAILED'}")
    print(f"  UE5 Integration: {'OK READY' if ue5_ready else 'FAIL NOT READY'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
