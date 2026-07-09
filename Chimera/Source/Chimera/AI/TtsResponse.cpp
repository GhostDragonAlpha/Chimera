// Copyright 2026 Chimera Project. All Rights Reserved.

#include "TtsResponse.h"
#include "Components/AudioComponent.h"
#include "Engine/World.h"
#include "Sound/SoundWave.h"
#include "Kismet/GameplayStatics.h"
#include "Components/AudioComponent.h"
#include "Components/AudioComponent.h"
#include "Engine/World.h"
#include "Async/Async.h"

UTtsResponse::UTtsResponse()
{
	CrispAsrSession = nullptr;
	CurrentSoundWave = nullptr;
	CurrentAudioComponent = nullptr;
	bIsBusy = false;
	VoiceInstruct = TEXT("A calm, professional female voice with a slight American accent");
}

UTtsResponse::~UTtsResponse()
{
	CleanupCrispAsrSession();
	
	if (CurrentAudioComponent)
	{
		CurrentAudioComponent->Stop();
		CurrentAudioComponent = nullptr;
	}
}

FVoiceActionResult UTtsResponse::GenerateResponse(const FString& Text)
{
	FVoiceActionResult Result;
	Result.bSuccess = false;
	Result.ResponseText = TEXT("TTS unavailable.");
	
	if (bIsBusy)
	{
		Result.ResponseText = TEXT("Still processing previous command. Please wait...");
		return Result;
	}

	bIsBusy = true;
	LastResponseText = Text;
	
	UE_LOG(LogTemp, Log, TEXT("[TTS] Generating response for: %s"), *Text);

	// ─── Try CrispASR first (Phase 3.2) ─────────────────────────────
	TArray<uint8> PcmData;
	if (InitCrispAsrSession())
	{
		PcmData = SynthesizeWithCrispAsr(Text);
		
		if (!PcmData.IsEmpty())
		{
			Result.bSuccess = PlayPcmAudio(PcmData, 24000); // CrispASR outputs at 24kHz
			Result.ResponseText = TEXT("Voice response generated.");
			Result.DetailLog = FString::Printf(TEXT("[TTS] Synthesized %d bytes of PCM audio"), PcmData.Num());
		}
		
		CleanupCrispAsrSession();
	}

	// ─── Fallback to UE5 built-in TTS (Phase 3.1) ──────────────────
	if (!Result.bSuccess && bUseBuiltInFallback)
	{
		Result.bSuccess = PlayWithBuiltInTts(Text);
		Result.ResponseText = Result.bSuccess ? TEXT("Voice response generated (built-in).") : TEXT("TTS failed.");
	}

	bIsBusy = false;
	
	if (!Result.bSuccess)
	{
		Result.DetailLog = FString::Printf(TEXT("[TTS] Failed to generate audio for: %s"), *Text);
		UE_LOG(LogTemp, Warning, TEXT("%s"), *Result.DetailLog);
	}

	return Result;
}

void UTtsResponse::StopCurrentPlayback()
{
	if (CurrentAudioComponent)
	{
		CurrentAudioComponent->Stop();
		CurrentAudioComponent = nullptr;
	}
	
	if (CurrentSoundWave)
	{
		CurrentSoundWave = nullptr;
	}
}

bool UTtsResponse::IsBusy() const
{
	return bIsBusy;
}

// ─── CrispASR Integration (Phase 3.2) ──────────────────────────────

bool UTtsResponse::InitCrispAsrSession()
{
	// TODO: Implement actual CrispASR C-ABI integration
	// This is a placeholder that will be replaced with real CrispASR calls
	
	/*
	// Example of what the real implementation would look like:
	#include "crispasr.h"  // CrispASR C-ABI header
	
	CrispAsrSession = (void*)crispasr_session_open(
		"qwen3-tts-1.7b-voicedesign",
		"auto",  // Model path (auto downloads from HuggingFace)
		VoiceInstruct.GetCharArray().GetData(),
		nullptr  // Codec model path (auto)
	);
	
	if (!CrispAsrSession)
	{
		UE_LOG(LogTemp, Warning, TEXT("[TTS] Failed to initialize CrispASR session"));
		return false;
	}
	*/
	
	// For now, return true but don't actually do anything
	// This allows the rest of the pipeline to work in testing mode
	UE_LOG(LogTemp, Log, TEXT("[TTS] CrispASR session initialized (placeholder)"));
	return true;
}

TArray<uint8> UTtsResponse::SynthesizeWithCrispAsr(const FString& Text)
{
	TArray<uint8> PcmData;
	
	// TODO: Implement actual CrispASR synthesis
	/*
	float* PcmFloat = nullptr;
	int32 NumSamples = 0;
	
	PcmFloat = crispasr_session_synthesize(
		(void*)CrispAsrSession,
		Text.GetCharArray().GetData(),
		&PcmData.Num()
	);
	
	if (PcmFloat && PcmData.Num > 0)
	{
		// Convert float32 PCM to uint8 buffer for UE5 audio pipeline
		int32 ByteCount = PcmData.Num * sizeof(float);
		PcmData.AddUninitialized(ByteCount);
		FMemory::Memcpy(PcmData.GetData(), PcmFloat, ByteCount);
		
		// Free CrispASR's allocated memory
		crispasr_session_free_pcm(PcmFloat);
	}
	*/
	
	return PcmData;  // Empty for now (placeholder)
}

void UTtsResponse::CleanupCrispAsrSession()
{
	if (CrispAsrSession)
	{
		// TODO: Call crispasr_session_close()
		CrispAsrSession = nullptr;
	}
}

// ─── UE5 Audio Pipeline Integration ────────────────────────────────

bool UTtsResponse::PlayPcmAudio(const TArray<uint8>& PcmData, int32 SampleRate)
{
	if (PcmData.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("[TTS] No PCM data to play"));
		return false;
	}

	// ─── Resample from 24kHz to 48kHz if needed ──────────────────────
	TArray<float> FloatData;
	if (SampleRate != TARGET_SAMPLE_RATE)
	{
		FloatData = ResampleFloat(
			(float*)PcmData.GetData(),
			SampleRate,
			TARGET_SAMPLE_RATE,
			PcmData.Num() / sizeof(float)
		);
	}
	else
	{
		// Already at target rate, just copy
		FloatData.AddUninitialized(PcmData.Num() / sizeof(float));
		FMemory::Memcpy(FloatData.GetData(), PcmData.GetData(), PcmData.Num());
	}

	// ─── Convert float32 to int16 for USoundWave ─────────────────────
	TArray<uint8> Int16Data = FloatToInt16(FloatData);
	
	if (Int16Data.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("[TTS] Failed to convert PCM to int16"));
		return false;
	}

	// ─── Create USoundWave with the audio data ──────────────────────
	USoundWave* SoundWave = NewObject<USoundWave>(GetTransientPackage(), NAME_None, RF_Transient);
	if (!SoundWave)
	{
		UE_LOG(LogTemp, Warning, TEXT("[TTS] Failed to create USoundWave"));
		return false;
	}

	// Set sound wave properties (UE5.8 API)
	SoundWave->NumChannels = 1;  // Mono
	SoundWave->Duration = (float)Int16Data.Num() / ((float)TARGET_SAMPLE_RATE * SoundWave->NumChannels);
	
	// Convert to float32 for UE5 sound wave (UE5.8 uses float32 internally)
	TArray<float> FloatSamples;
	FloatSamples.AddUninitialized(Int16Data.Num() / sizeof(int16));
	for (int32 i = 0; i < Int16Data.Num() / sizeof(int16); ++i)
	{
		// Convert int16 to float (-1.0f to 1.0f range)
		int16 Sample = *reinterpret_cast<const int16*>(Int16Data.GetData() + i * sizeof(int16));
		FloatSamples[i] = (float)Sample / 32768.0f;
	}
	
	// Set the audio data using UE5.8 compatible method
	// Note: USoundWave uses internal bulk data that we can't directly access in UE5.8
	// For now, we'll just set basic properties and let UE handle the rest

	// ─── Create audio component and play ─────────────────────────────
	AActor* Owner = nullptr;  // Would be set from VoiceEntity
	
	if (Owner)
	{
		// Use UGameplayStatics to create and play sound effect
		UGameplayStatics::PlaySound2D(GetWorld(), SoundWave, VolumeMultiplier);
		
		UE_LOG(LogTemp, Log, TEXT("[TTS] Playing audio: %d samples at %d Hz"), 
			Int16Data.Num() / sizeof(int16), TARGET_SAMPLE_RATE);
		
		CurrentSoundWave = SoundWave;
		return true;
	}

	// If no owner actor, just log success (audio would play in editor)
	UE_LOG(LogTemp, Log, TEXT("[TTS] USoundWave created but no owner to attach audio component"));
	return false;
}

TArray<float> UTtsResponse::ResampleFloat(float* Source, int32 SourceRate, int32 TargetRate, int32 NumSamples)
{
	// Simple linear resampling (not optimal for quality, but sufficient for TTS)
	TArray<float> Resampled;
	
	float Ratio = (float)SourceRate / (float)TargetRate;
	int32 NewNumSamples = NumSamples * ((float)TargetRate / (float)SourceRate);
	
	Resampled.AddUninitialized(NewNumSamples);
	
	for (int32 i = 0; i < NewNumSamples; i++)
	{
		float SourceIndex = i * Ratio;
		int32 Index1 = FMath::FloorToInt(SourceIndex);
		int32 Index2 = FMath::CeilToInt(SourceIndex);
		
		if (Index1 >= NumSamples) Index1 = NumSamples - 1;
		if (Index2 >= NumSamples) Index2 = NumSamples - 1;
		
		float Fraction = SourceIndex - Index1;
		Resampled[i] = Source[Index1] * (1.0f - Fraction) + Source[Index2] * Fraction;
	}
	
	return Resampled;
}

TArray<uint8> UTtsResponse::FloatToInt16(const TArray<float>& FloatData)
{
	if (FloatData.Num() == 0) return TArray<uint8>();
	
	TArray<uint8> Int16Data;
	Int16Data.AddUninitialized(FloatData.Num() * sizeof(int16));
	
	for (int32 i = 0; i < FloatData.Num(); i++)
	{
		// Clamp to [-1.0, 1.0] and convert to int16 range [-32768, 32767]
		float Clamped = FMath::Clamp(FloatData[i], -1.0f, 1.0f);
		int16 Sample = (int16)(Clamped * 32767.0f);
		
		// Store as little-endian bytes
		uint8* Bytes = Int16Data.GetData() + (i * sizeof(int16));
		Bytes[0] = Sample & 0xFF;        // Low byte
		Bytes[1] = (Sample >> 8) & 0xFF;  // High byte
	}
	
	return Int16Data;
}

// ─── UE5 Built-In TTS Fallback (Phase 3.1) ────────────────────────

bool UTtsResponse::PlayWithBuiltInTts(const FString& Text)
{
	// TODO: Implement UE5's built-in TextToSpeech plugin integration
	/*
	Example implementation:
	
	UTextToSpeechSubsystem* TtsSubsystem = UGameplayStatics::GetTextToSpeechSubsystem(GetWorld());
	if (TtsSubsystem)
	{
		FString ChannelId = TEXT("VoiceEntityChannel");
		
		TtsSubsystem->AddDefaultChannel(ChannelId);
		TtsSubsystem->ActivateChannel(ChannelId);
		TtsSubsystem->SpeakOnChannel(Text, ChannelId);
		
		return true;
	}
	*/
	
	UE_LOG(LogTemp, Warning, TEXT("[TTS] Built-in TTS not implemented yet (placeholder)"));
	return false;
}
