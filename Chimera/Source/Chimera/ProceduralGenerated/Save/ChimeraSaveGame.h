#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "ChimeraSaveGame.generated.h"

/**
 * Player state data structure for save system.
 */
USTRUCT(BlueprintType)
struct FChimeraPlayerState
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, SaveGame)
	float Health;

	UPROPERTY(BlueprintReadWrite, SaveGame)
	float MaxHealth;

	UPROPERTY(BlueprintReadWrite, SaveGame)
	float Shield;

	UPROPERTY(BlueprintReadWrite, SaveGame)
	float MaxShield;

	UPROPERTY(BlueprintReadWrite, SaveGame)
	FVector Location;

	UPROPERTY(BlueprintReadWrite, SaveGame)
	FRotator Rotation;

	FChimeraPlayerState()
		: Health(100.f), MaxHealth(100.f), Shield(0.f), MaxShield(0.f), Location(FVector::ZeroVector), Rotation(FRotator::ZeroRotator)
	{
	}
};

/**
 * Inventory item data structure for save system.
 */
USTRUCT(BlueprintType)
struct FChimeraInventoryItem
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, SaveGame)
	FString ItemName;

	UPROPERTY(BlueprintReadWrite, SaveGame)
	int32 Quantity;

	FChimeraInventoryItem()
		: Quantity(0)
	{
	}
};

/**
 * Main save game data structure for Chimera project.
 */
UCLASS()
class CHIMERA_API UChimeraSaveGame : public USaveGame
{
	GENERATED_BODY()

public:
	UChimeraSaveGame();

	// Game state data
	UPROPERTY(SaveGame)
	FString SaveVersion;

	UPROPERTY(SaveGame)
	FDateTime LastSavedTime;

	// Player state data
	UPROPERTY(SaveGame)
	FChimeraPlayerState PlayerState;

	// Ship state data
	UPROPERTY(SaveGame)
	FString CurrentShipName;

	UPROPERTY(SaveGame)
	TArray<FString> OwnedShips;

	// Inventory data
	UPROPERTY(SaveGame)
	TArray<FChimeraInventoryItem> InventoryItems;

	// Mission state data
	UPROPERTY(SaveGame)
	TArray<FString> CompletedMissions;

	UPROPERTY(SaveGame)
	TArray<FString> ActiveMissions;

	// Faction reputation data
	UPROPERTY(SaveGame)
	TMap<FString, int32> FactionReputation;
};
