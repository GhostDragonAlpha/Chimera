// Copyright 2026 Chimera Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "VoiceCommandStructs.h"
#include "TtsResponse.generated.h"

/**
 * TTS Response System — Bridges Qwen3-TTS (via CrispASR C-ABI) with UE5 audio pipeline.
 * 
 * Phase 3 implementation: Converts text responses into playable audio for the player.
 * 
 * Architecture:
 *   [Text response] → [CrispASR TTS engine] → [PCM float32 @ 24kHz]
 *     → [Audio conversion layer] → [USoundWave creation] → [UAudioComponent playback]
 * 
 * Quick Start (Phase 3.1): Use UE5's built-in TextToSpeech plugin (CMU Flite)
 * Production Path (Phase 3.2): Use Qwen3-TTS-12Hz-1.7B-VoiceDesign via CrispASR C-ABI
 */
UCLASS(BlueprintType, meta = (BlueprintThreadSafe))
class CHIMERA_API UTtsResponse : public UObject
{
	GENERATED_BODY()

public:
	UTtsResponse();
	~UTtsResponse();

	/**
	 * Generate a TTS response for the given text.
	 * @param Text The text to synthesize (e.g., "Spawned rock at your location.")
	 * @return FVoiceActionResult with bSuccess=true if audio was generated
	 */
	UFUNCTION(BlueprintCallable, Category = "Chimera|TTS")
	FVoiceActionResult GenerateResponse(const FString& Text);

	/**
	 * Stop any currently playing TTS audio.
	 */
	UFUNCTION(BlueprintCallable, Category = "Chimera|TTS")
	void StopCurrentPlayback();

	/**
	 * Check if TTS is currently synthesizing or playing.
	 */
	UFUNCTION(BlueprintPure, Category = "Chimera|TTS")
	bool IsBusy() const;

private:
	// ─── CrispASR integration (Phase 3.2) ──────────────────────────

	/** Initialize CrispASR session with Qwen3-TTS model */
	bool InitCrispAsrSession();

	/** Synthesize text to PCM using CrispASR C-ABI */
	TArray<uint8> SynthesizeWithCrispAsr(const FString& Text);

	/** Cleanup CrispASR session */
	void CleanupCrispAsrSession();

	// ─── UE5 audio pipeline integration ─────────────────────────────

	/** Convert PCM float32 to USoundWave and play it */
	bool PlayPcmAudio(const TArray<uint8>& PcmData, int32 SampleRate);

	/** Resample from source rate to target rate (48kHz) */
	TArray<float> ResampleFloat(float* Source, int32 SourceRate, int32 TargetRate, int32 NumSamples);

	/** Convert float32 PCM to int16 for USoundWave */
	TArray<uint8> FloatToInt16(const TArray<float>& FloatData);

	// ─── UE5 built-in TTS fallback (Phase 3.1) ──────────────────────

	/** Use UE5's TextToSpeech plugin as quick-start fallback */
	bool PlayWithBuiltInTts(const FString& Text);

	// ─── State tracking ─────────────────────────────────────────────

	UPROPERTY()
	UObject* CrispAsrSession;  // Opaque pointer to CrispASR session (void*)

	UPROPERTY()
	UObject* CurrentSoundWave;  // Currently playing USoundWave

	UPROPERTY()
	UAudioComponent* CurrentAudioComponent;  // Component playing the sound

	UPROPERTY()
	bool bIsBusy;  // True while synthesizing or playing audio

	UPROPERTY()
	FString LastResponseText;  // Most recent text that was synthesized

	// ─── Configuration ──────────────────────────────────────────────

	UPROPERTY(EditAnywhere, Category = "TTS|Configuration")
	FString VoiceInstruct;  // Natural language voice description for Qwen3-TTS VoiceDesign

	UPROPERTY(EditAnywhere, Category = "TTS|Configuration")
	bool bUseBuiltInFallback = true;  // Use UE5's TextToSpeech plugin if CrispASR fails

	UPROPERTY(EditAnywhere, Category = "TTS|Configuration")
	float VolumeMultiplier = 1.0f;  // Audio volume (0.0 to 2.0)

	// ─── Constants ──────────────────────────────────────────────────

	static constexpr int32 TARGET_SAMPLE_RATE = 48000;  // UE5 engine default
	static constexpr float MAX_SYNTHESIS_TIME_MS = 10000.0f;  // 10 second timeout
};
