// Copyright 2026 Chimera Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
class UWhisperWrapper;  // Forward declaration
#include "SttEngine.generated.h"

/**
 * Speech-to-Text Engine Interface — Abstract base for STT backends.
 * 
 * Phase 2 implementation: Converts microphone audio input to text commands.
 * Supports multiple backends (Whisper via whisper.cpp, LM Studio/Qwen2-Audio, AzureSTT) via strategy pattern.
 */
UCLASS(BlueprintType, meta = (BlueprintThreadSafe))
class CHIMERA_API USttEngine : public UObject
{
	GENERATED_BODY()

public:
	USttEngine();
	~USttEngine();

	/**
	 * Initialize the STT engine with specified backend.
	 * @param BackendType "whisper" or "lm_studio" or "azure_stt"
	 * @return True if initialization succeeded
	 */
	UFUNCTION(BlueprintCallable, Category = "Chimera|STT")
	bool InitEngine(const FString& BackendType);

	/**
	 * Process audio input and return transcribed text.
	 * @param AudioData Raw PCM audio data (16-bit, mono, 16kHz)
	 * @return Transcribed text string
	 */
	UFUNCTION(BlueprintCallable, Category = "Chimera|STT")
	FString ProcessAudio(const TArray<uint8>& AudioData);

	/**
	 * Check if STT engine is ready and initialized.
	 */
	UFUNCTION(BlueprintPure, Category = "Chimera|STT")
	bool IsReady() const;

protected:
	// ─── Backend implementations ──────────────────────────────────────

	/** Whisper.cpp backend (local C++ library) */
	FString ProcessWithWhisper(const TArray<uint8>& AudioData);

	/** LM Studio + Qwen2-Audio backend (local HTTP API) */
	FString ProcessWithLmStudio(const TArray<uint8>& AudioData);

	/** Azure Speech-to-Text backend (cloud-based) */
	FString ProcessWithAzureStt(const TArray<uint8>& AudioData);

	// ─── State tracking ───────────────────────────────────────────────

	void* WhisperEngine;  // Placeholder for UWhisperWrapper instance

	void* HttpModule;  // Placeholder for future HTTP module integration

	UPROPERTY()
	FString CurrentBackend;  // "whisper", "lm_studio", or "azure_stt"

	UPROPERTY()
	bool bIsReady;  // True if engine is initialized and ready

	// ─── Configuration ────────────────────────────────────────────────

	UPROPERTY(EditAnywhere, Category = "STT|Configuration")
	FString WhisperModelPath = TEXT("E:/PythonChimera/Chimera/Content/AIModels/ggml-base.en.bin");  // Path to whisper.cpp model file

	UPROPERTY(EditAnywhere, Category = "STT|Configuration")
	FString LmStudioUrl = TEXT("http://localhost:1234/v1/chat/completions");  // LM Studio server URL

	UPROPERTY(EditAnywhere, Category = "STT|Configuration")
	FString LmStudioModelName = TEXT("qwen2-audio-7b-instruct");  // Model identifier in LM Studio

	UPROPERTY(EditAnywhere, Category = "STT|Configuration")
	float AudioThreshold = 0.1f;  // Minimum audio energy to trigger recording

	UPROPERTY(EditAnywhere, Category = "STT|Configuration")
	int32 SampleRate = 16000;  // Target sample rate for STT (Hz)
};
