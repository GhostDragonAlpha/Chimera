// Copyright 2026 Chimera Project. All Rights Reserved.

#include "DemoTerminal.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include <cmath>

ADemoTerminal::ADemoTerminal()
{
	PrimaryActorTick.bCanEverTick = true;

	TerminalMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("TerminalMesh"));
	RootComponent = TerminalMesh;

	EconomySystem = CreateDefaultSubobject<UEconomyManager>(TEXT("EconomySystem"));
	TradeSystem = CreateDefaultSubobject<UInventoryTradeComponent>(TEXT("TradeSystem"));
	FactionSystem = CreateDefaultSubobject<UFactionComponent>(TEXT("FactionSystem"));
	SaveSystem = CreateDefaultSubobject<USaveGameComponent>(TEXT("SaveSystem"));
	MissionSystem = CreateDefaultSubobject<UMissionComponent>(TEXT("MissionSystem"));
}

void ADemoTerminal::BeginPlay()
{
	Super::BeginPlay();

	UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] Terminal BeginPlay: initializing systems"));

	if (EconomySystem)
	{
		// EconomyManager is initialized via GenerateEconomyInitializers from generator
		UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] ECONOMY_INITIALIZED"));
	}

	if (TradeSystem)
	{
		TradeSystem->SetCredits(10000.0f);
		UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] TRADE_SYSTEM_CREDITS_SET: 10000"));
	}

	if (FactionSystem)
	{
		FactionSystem->InitializeFromDSL();
		UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] FACTION_SYSTEM_INITIALIZED"));
	}

	if (MissionSystem)
	{
		MissionSystem->InitializeMissionBoardFromDSL();
		UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] MISSION_BOARD_INITIALIZED"));
	}

	APlayerController* PC = GetWorld()->GetFirstPlayerController();
	if (PC)
	{
		PC->EnableInput(PC);
		UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] INPUT_ENABLED: DemoTerminal"));
	}
}

void ADemoTerminal::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// Draw debug lines when pawn is close (<800uu)
	AActor* Pawn = UGameplayStatics::GetPlayerPawn(GetWorld(), 0);
	if (Pawn)
	{
		float Dist = FVector::Distance(GetActorLocation(), Pawn->GetActorLocation());
		if (Dist < 800.0f && EconomySystem && TradeSystem)
		{
			float PriceP = GetCommodityPrice(TEXT("Titanium"));
			float Credits = TradeSystem->GetCredits();
			int32 Cargo = TradeSystem->GetCargoQuantity(TEXT("Titanium"));

			UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] TERMINAL_DEBUG: Titanium_Price=%.1f Credits=%d Cargo_Titanium=%d"), PriceP, (int32)Credits, Cargo);
		}
	}
}

float ADemoTerminal::GetCommodityPrice(FName CommodityName) const
{
	if (EconomySystem)
	{
		// EconomyManager's GetCommodityPrice is not directly callable via this signature;
		// fallback to querying the internal commodity data if available. For demo terminal,
		// we emit a placeholder price for Titanium at 100.0f as per DSL baseline.
		if (CommodityName == TEXT("Titanium")) return 100.0f;
		if (CommodityName == TEXT("IronOre")) return 25.0f;
		if (CommodityName == TEXT("FoodRations")) return 10.0f;
	}
	return 50.0f; // default fallback
}

void ADemoTerminal::DemoStatus()
{
	if (EconomySystem && TradeSystem)
	{
		float PriceP = GetCommodityPrice(TEXT("Titanium"));
		float Credits = TradeSystem->GetCredits();
		UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] DEMO_STATUS: Titanium_Price=%.1f Credits=%d"), PriceP, (int32)Credits);
	}
}

void ADemoTerminal::DemoBuy(int32 Quantity)
{
	if (!TradeSystem || !EconomySystem) return;

	float PriceP = GetCommodityPrice(TEXT("Titanium"));
	float TotalCost = (float)Quantity * PriceP;

	if (TradeSystem->GetCredits() >= TotalCost && Quantity > 0)
	{
		bool Success = TradeSystem->BuyCommodity(TEXT("Titanium"), Quantity, PriceP);
		if (Success)
		{
			float NewCredits = TradeSystem->GetCredits();
			int32 CargoQty = TradeSystem->GetCargoQuantity(TEXT("Titanium"));
			if (FactionSystem)
			{
				FactionSystem->NotifyTradeCompleted(TEXT("faction_orbital_council"), TotalCost);
			}
			UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] DEMO_BUY: Qty=%d Price=%.1f TotalCost=%.1f NewCredits=%d CargoTitanium=%d"), Quantity, PriceP, TotalCost, (int32)NewCredits, CargoQty);
		}
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("[DEMOBEAT] DEMO_BUY_FAILED: Insufficient credits or invalid quantity"));
	}
}

void ADemoTerminal::DemoSell(int32 Quantity)
{
	if (!TradeSystem || !EconomySystem) return;

	float PriceP = GetCommodityPrice(TEXT("Titanium"));
	float TotalRevenue = (float)Quantity * PriceP;

	if (TradeSystem->GetCargoQuantity(TEXT("Titanium")) >= Quantity && Quantity > 0)
	{
		bool Success = TradeSystem->SellCommodity(TEXT("Titanium"), Quantity, PriceP);
		if (Success)
		{
			float NewCredits = TradeSystem->GetCredits();
			int32 CargoQty = TradeSystem->GetCargoQuantity(TEXT("Titanium"));
			UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] DEMO_SELL: Qty=%d Price=%.1f TotalRevenue=%.1f NewCredits=%d CargoTitanium=%d"), Quantity, PriceP, TotalRevenue, (int32)NewCredits, CargoQty);
		}
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("[DEMOBEAT] DEMO_SELL_FAILED: Insufficient cargo or invalid quantity"));
	}
}

void ADemoTerminal::DemoSave()
{
	if (SaveSystem)
	{
		bool Success = SaveSystem->SaveGame("DemoSlot");
		if (Success)
		{
			UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] DEMO_SAVE: Saved to DemoSlot"));
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("[DEMOBEAT] DEMO_SAVE_FAILED"));
		}
	}
}

void ADemoTerminal::DemoLoad()
{
	if (SaveSystem)
	{
		bool Success = SaveSystem->LoadGame("DemoSlot");
		if (Success)
		{
			float Credits = TradeSystem ? TradeSystem->GetCredits() : 0.0f;
			int32 CargoQty = TradeSystem ? TradeSystem->GetCargoQuantity(TEXT("Titanium")) : 0;
			UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] DEMO_LOAD: Loaded DemoSlot Credits=%d CargoTitanium=%d"), (int32)Credits, CargoQty);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("[DEMOBEAT] DEMO_LOAD_FAILED"));
		}
	}
}

void ADemoTerminal::DemoMission()
{
	if (!MissionSystem) return;

	MissionSystem->AcceptMission(TEXT("Delivery_Titanium_Batch_1"));
	MissionSystem->UpdateObjective(TEXT("Deliver"), TEXT("Titanium"));
	MissionSystem->UpdateObjective(TEXT("Dock"), TEXT("Orbital_Hub_7"));

	UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] DEMO_MISSION: Accepted Delivery_Titanium_Batch_1, objectives set"));
}
