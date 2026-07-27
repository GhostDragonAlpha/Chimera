// Copyright 2026 Chimera Project. All Rights Reserved.

#include "SttEngine.h"

USttEngine::USttEngine()
{
	WhisperEngine = nullptr;
	HttpModule = nullptr;
	bIsReady = false;
}

USttEngine::~USttEngine()
{
	// Cleanup resources if needed
	if (WhisperEngine)
	{
		WhisperEngine = nullptr;  // Placeholder - no actual allocation
	}
}

bool USttEngine::InitEngine(const FString& BackendType)
{
	CurrentBackend = BackendType;
	
	if (BackendType == TEXT("whisper"))
	{
		// Initialize whisper.cpp backend
		UE_LOG(LogTemp, Log, TEXT("[STT] Initializing Whisper backend with model: %s"), *WhisperModelPath);
		
		// TODO: Create and initialize WhisperEngine instance
		// For now, we'll just mark as ready for testing
		bIsReady = true;
		
		UE_LOG(LogTemp, Log, TEXT("[STT] Whisper backend initialized successfully"));
		return true;
	}
	else if (BackendType == TEXT("lm_studio"))
	{
		// Initialize LM Studio + Qwen2-Audio backend
		UE_LOG(LogTemp, Log, TEXT("[STT] Initializing LM Studio backend at: %s"), *LmStudioUrl);
		
		// TODO: Set up HTTP module and connection to LM Studio
		bIsReady = true;
		
		UE_LOG(LogTemp, Log, TEXT("[STT] LM Studio backend initialized successfully"));
		return true;
	}
	else if (BackendType == TEXT("azure_stt"))
	{
		// Initialize Azure Speech-to-Text backend
		UE_LOG(LogTemp, Warning, TEXT("[STT] Azure STT backend not yet implemented"));
		
		bIsReady = false;
		return false;
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("[STT] Unknown backend type: %s"), *BackendType);
		return false;
	}
}

FString USttEngine::ProcessAudio(const TArray<uint8>& AudioData)
{
	if (!bIsReady)
	{
		UE_LOG(LogTemp, Warning, TEXT("[STT] Engine not ready - cannot process audio"));
		return TEXT("Speech-to-text engine not available");
	}

	if (AudioData.Num() == 0)
	{
		UE_LOG(LogTemp, Warning, TEXT("[STT] Empty audio data received"));
		return TEXT("");
	}

	if (CurrentBackend == TEXT("whisper"))
	{
		return ProcessWithWhisper(AudioData);
	}
	else if (CurrentBackend == TEXT("lm_studio"))
	{
		return ProcessWithLmStudio(AudioData);
	}
	else if (CurrentBackend == TEXT("azure_stt"))
	{
		return ProcessWithAzureStt(AudioData);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("[STT] No valid backend configured"));
		return TEXT("");
	}
}

bool USttEngine::IsReady() const
{
	return bIsReady;
}

FString USttEngine::ProcessWithWhisper(const TArray<uint8>& AudioData)
{
	if (!WhisperEngine)
	{
		UE_LOG(LogTemp, Warning, TEXT("[STT] Whisper engine not initialized"));
		return TEXT("Whisper engine not ready");
	}

	// Process audio through whisper.cpp (stub implementation)
	// TODO: Integrate with actual whisper.cpp library when build system is configured
	UE_LOG(LogTemp, Warning, TEXT("[STT] Whisper.cpp integration pending - stub mode active"));
	return TEXT("Speech-to-text engine not fully available");
}

FString USttEngine::ProcessWithLmStudio(const TArray<uint8>& AudioData)
{
	// TODO: Implement LM Studio + Qwen2-Audio backend
	UE_LOG(LogTemp, Warning, TEXT("[STT] LM Studio STT not yet implemented"));
	return TEXT("LM Studio STT not available");
}

FString USttEngine::ProcessWithAzureStt(const TArray<uint8>& AudioData)
{
	// TODO: Implement Azure Speech-to-Text backend
	UE_LOG(LogTemp, Warning, TEXT("[STT] Azure STT not yet implemented"));
	return TEXT("Azure STT not available");
}
