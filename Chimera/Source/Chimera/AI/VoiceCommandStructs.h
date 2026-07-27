// Copyright 2026 Chimera Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "VoiceCommandStructs.generated.h"

/**
 * Action types the Voice entity can execute.
 */
UENUM(BlueprintType)
enum class EVoiceActionType : uint8
{
	// World manipulation
	SpawnActor,
	DeleteActor,
	DuplicateActor,
	MoveActor,
	RotateActor,
	ScaleActor,

	// Property modification
	ModifyProperty,
	QueryProperty,

	// Game state
	SaveGame,
	LoadGame,
	SetGravity,
	SetTimeDilation,

	// Economy / Mission (wraps DemoTerminal)
	EconomyBuy,
	EconomySell,
	EconomyStatus,
	MissionAccept,
	MissionStatus,

	// Query / Information
	QueryWorld,
	QueryPlayer,
	ListActors,

Unknown UMETA(ToolTip = "Could not determine intent; route to Pi agent")
};

/**
 * Structured voice action after NLP parsing.
 */
USTRUCT(BlueprintType)
struct CHIMERA_API FVoiceAction
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice|Action")
	EVoiceActionType Type = EVoiceActionType::Unknown;

	/** What to act on (actor name, property path, commodity name) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice|Action")
	FString Target;

	/** Where to spawn/move */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice|Action")
	FVector Location = FVector::ZeroVector;

	/** Direction for movement commands */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice|Action")
	FVector Direction = FVector::ZeroVector;

	/** Value to set (e.g., brightness, gravity scale) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice|Action")
	float PropertyValue = 0.0f;

	/** Which property to modify */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice|Action")
	FName PropertyName;

	/** Quantity for economy commands (e.g., buy 100 titanium) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice|Action")
	int32 Quantity = 0;

	/** Free-text query for LLM fallback */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice|Action")
	FString QueryText;

	/** Original user utterance (for logging/debug) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice|Action")
	FString OriginalUtterance;

	FVoiceAction()
	{
		Type = EVoiceActionType::Unknown;
		Location = FVector::ZeroVector;
		Direction = FVector::ZeroVector;
		PropertyValue = 0.0f;
		Quantity = 0;
	}
};

/**
 * Result of executing a voice action.
 */
USTRUCT(BlueprintType)
struct CHIMERA_API FVoiceActionResult
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice|Result")
	bool bSuccess = false;

	/** Human-readable response text (for TTS display) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice|Result")
	FString ResponseText;

	/** Detailed log message */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice|Result")
	FString DetailLog;

	FVoiceActionResult()
	{
		bSuccess = false;
	}
};
