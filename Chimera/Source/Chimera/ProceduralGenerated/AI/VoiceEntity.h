// Copyright 2026 Chimera Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/TextRenderComponent.h"
#include "../Economy/EconomyManager.h"
#include "../Inventory/InventoryTradeComponent.h"
#include "../Factions/FactionComponent.h"
#include "../Save/SaveGameComponent.h"
#include "../Missions/MissionComponent.h"
#include "../../AI/NlpParser.h"
#include "../../AI/SttEngine.h"
#include "VoiceEntity.generated.h"

class USocialTradeComponent;
class UNPCTradeComponent;

/**
 * AChimeraVoiceEntity — The in-game AI entity that processes voice commands.
 * 
 * This is the player-facing "computer" they can talk to, like Star Trek's computer
 * or JARVIS. It wraps all game subsystems (economy, trade, missions, save/load)
 * and exposes them through natural language voice commands.
 * 
 * Phase 1: Console command interface (text input via UE console)
 * Phase 2: Speech-to-text integration (microphone → STT → NLP)
 * Phase 3: Text-to-speech responses (audio feedback to player)
 * Phase 4: Pi agent integration (LLM-enhanced queries)
 */
UCLASS(Blueprintable)
class CHIMERA_API AVoiceEntity : public AActor
{
	GENERATED_BODY()

public:
	AVoiceEntity();

protected:
	virtual void Tick(float DeltaTime) override;
	virtual void BeginPlay() override;

public:
	// ─── Visual representation ──────────────────────────────────────

	UPROPERTY(VisibleAnywhere, Category = "Voice|Visual")
	UStaticMeshComponent* VoiceMesh;

	UPROPERTY(VisibleAnywhere, Category = "Voice|Visual")
	UTextRenderComponent* StatusDisplay;

	// ─── Audio feedback (Phase 3) ───────────────────────────────────

	UPROPERTY(EditAnywhere, Category = "Voice|Audio")
	USoundCue* VoiceStartSound;  // Audio cue when listening starts

	UPROPERTY(EditAnywhere, Category = "Voice|Audio")
	USoundCue* VoiceEndSound;    // Audio cue when processing complete

	// ─── Subsystem references (like DemoTerminal but extended) ──────

	UPROPERTY(BlueprintReadOnly, Category = "Voice|Systems")
	UEconomyManager* EconomySystem;

	UPROPERTY(BlueprintReadOnly, Category = "Voice|Systems")
	UInventoryTradeComponent* TradeSystem;

	UPROPERTY(BlueprintReadOnly, Category = "Voice|Systems")
	UFactionComponent* FactionSystem;

	UPROPERTY(BlueprintReadOnly, Category = "Voice|Systems")
	USaveGameComponent* SaveSystem;

	UPROPERTY(BlueprintReadOnly, Category = "Voice|Systems")
	UMissionComponent* MissionSystem;

	// ─── NLP Parser ────────────────────────────────────────────────

	UPROPERTY(BlueprintReadWrite, Category = "Voice|NLP")
	UNlpParser* NlpParserInstance;

	// ─── STT Engine (Phase 2) ──────────────────────────────────────

	UPROPERTY(BlueprintReadWrite, Category = "Voice|STT")
	USttEngine* SttEngine;  // Speech-to-text engine for microphone input

	// ─── NPC trade behaviours (H-34: attached so the entity can trade with the player) ─

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Voice|Trade")
	USocialTradeComponent* SocialTradeComp;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Voice|Trade")
	UNPCTradeComponent* NPCTradeComp;

	// ─── Voice command processing (Phase 1: console-based) ─────────

	/**
	 * Main entry point for voice commands.
	 * Called from UE console via `ke <VoiceEntity> VoiceCommand "spawn a rock here"`
	 */
	UFUNCTION(Exec, Category = "Voice|Commands")
	void VoiceCommand(const FString& CommandText);

	/**
	 * Process audio input and transcribe it (Phase 2: microphone input).
	 * @param AudioData Raw PCM audio data (16-bit, mono, 16kHz)
	 */
	UFUNCTION(BlueprintCallable, Category = "Voice|STT")
	void VoiceCommandFromAudio(const TArray<uint8>& AudioData);

	/**
	 * Process a parsed voice action and execute it.
	 * Returns result struct with success flag and response text for TTS display.
	 */
	UFUNCTION(BlueprintCallable, Category = "Voice|Actions")
	FVoiceActionResult ExecuteVoiceAction(const FVoiceAction& Action);

	/**
	 * Get the current status of all subsystems (for economy/status queries).
	 */
	UFUNCTION(Exec, Category = "Voice|Commands")
	void VoiceStatus();

private:
	// ─── Action execution handlers ──────────────────────────────────

	FVoiceActionResult ExecuteSpawn(const FVoiceAction& Action);
	FVoiceActionResult ExecuteDelete(const FVoiceAction& Action);
	FVoiceActionResult ExecuteEconomyBuy(const FVoiceAction& Action);
	FVoiceActionResult ExecuteEconomySell(const FVoiceAction& Action);
	FVoiceActionResult ExecuteEconomyStatus();
	FVoiceActionResult ExecuteSaveGame();
	FVoiceActionResult ExecuteLoadGame();
	FVoiceActionResult ExecuteMissionAccept();
	FVoiceActionResult ExecuteQueryWorld(const FVoiceAction& Action);
	FVoiceActionResult ExecuteListActors();

	// ─── Helper methods ─────────────────────────────────────────────

	/** Get the player's current pawn for location-based commands */
	AActor* GetPlayerPawn() const;

	/** Spawn an actor at a given location with default transform */
	AActor* SpawnActorAtLocation(const FString& ActorClassPath, const FVector& Location);

	/** Find an actor near a given location by name */
	AActor* FindActorNearLocation(const FString& ActorName, const FVector& Location);

	/** Draw debug visualization when Voice entity is active */
	void DrawDebugVisualization(float DeltaTime);

	/** Log response to game log and print to player's screen */
	void RespondToPlayer(const FString& ResponseText, const FString& DetailLog = TEXT(""));

	// ─── State tracking ─────────────────────────────────────────────

	UPROPERTY()
	bool bIsProcessing;  // Prevents concurrent command processing

	UPROPERTY()
	FString LastResponse;  // Most recent response text (for StatusDisplay)

	UPROPERTY()
	float DebugVisualizationTimer;  // Timer for debug line drawing

	// ─── Default values ─────────────────────────────────────────────

	static constexpr float DEBUG_VISUALIZATION_RANGE = 800.0f;  // Units
};
