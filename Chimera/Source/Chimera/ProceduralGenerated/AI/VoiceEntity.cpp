// Copyright 2026 Chimera Project. All Rights Reserved.

#include "VoiceEntity.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "SocialTradeComponent.h"
#include "NPCTradeComponent.h"

AVoiceEntity::AVoiceEntity()
{
	// ─── Primary mesh component (visible in editor) ────────────────
	VoiceMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VoiceMesh"));
	RootComponent = VoiceMesh;
	VoiceMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	VoiceMesh->SetVisibility(true, true);

	// ─── Status display (text above entity) ────────────────────────
	StatusDisplay = CreateDefaultSubobject<UTextRenderComponent>(TEXT("StatusDisplay"));
	if (StatusDisplay)
	{
		StatusDisplay->SetupAttachment(RootComponent);
		StatusDisplay->SetRelativeLocation(FVector(0.0f, 0.0f, 120.0f));
		StatusDisplay->SetText(FText::FromString(TEXT("Voice Entity Ready")));
		StatusDisplay->SetVisibility(true, true);
	}

	// ─── NLP Parser instance ──────────────────────────────────────
	NlpParserInstance = CreateDefaultSubobject<UNlpParser>(TEXT("NlpParser"));

	// ─── STT Engine (Phase 2) ─────────────────────────────────────
	SttEngine = CreateDefaultSubobject<USttEngine>(TEXT("SttEngine"));

	// ─── NPC trade behaviours — the interactive entity can socially/NPC-trade
	//     with the player (H-34: components attached, not dead classes) ─
	SocialTradeComp = CreateDefaultSubobject<USocialTradeComponent>(TEXT("SocialTradeComp"));
	NPCTradeComp = CreateDefaultSubobject<UNPCTradeComponent>(TEXT("NPCTradeComp"));

	// Audio cues (Phase 3) — BP-assigned; played on listen-start / process-complete.
	VoiceStartSound = nullptr;
	VoiceEndSound = nullptr;

	// ─── Subsystem references (will be set by Blueprint or generator) ─
	EconomySystem = nullptr;
	TradeSystem = nullptr;
	FactionSystem = nullptr;
	SaveSystem = nullptr;
	MissionSystem = nullptr;

	// ─── State tracking ───────────────────────────────────────────
	bIsProcessing = false;
	DebugVisualizationTimer = 0.0f;

	// ─── Tick settings ────────────────────────────────────────────
	PrimaryActorTick.bCanEverTick = true;
}

void AVoiceEntity::BeginPlay()
{
	Super::BeginPlay();

	UE_LOG(LogTemp, Log, TEXT("[VoiceEntity] Voice Entity initialized at %s"), *GetActorLocation().ToString());
	UE_LOG(LogTemp, Log, TEXT("[VoiceEntity] Available commands: 'spawn a rock', 'buy titanium', 'save game', 'status', etc."));

	// ─── Initialize subsystem references (find in world) ──────────────
	// The subsystems are typically attached to other actors (e.g., stations, game mode)
	// Search for them in the world and cache references
	if (GetWorld())
	{
		// Note: These would be found dynamically at runtime
		// For now, log that they need to be manually assigned or found via cast
		UE_LOG(LogTemp, Warning, TEXT("[VoiceEntity] Subsystems not yet initialized - they must be assigned via Blueprint or dynamically found"));
	}

	// ─── Initialize NLP Parser if present ─────────────────────────────
	if (NlpParserInstance)
	{
		UE_LOG(LogTemp, Log, TEXT("[VoiceEntity] NLP Parser initialized"));
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("[VoiceEntity] NLP Parser not initialized - voice command parsing will be limited"));
	}

	// ─── Initialize STT Engine (Phase 2) ──────────────────────────────
	if (SttEngine)
	{
		// Note: Model path should be relative to the project content directory
		// or configurable via Blueprint/config files
		UE_LOG(LogTemp, Log, TEXT("[VoiceEntity] STT Engine component present - awaiting model initialization"));
		// SttEngine initialization will happen when model is available
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("[VoiceEntity] STT Engine not initialized - audio input will not work"));
	}

	UE_LOG(LogTemp, Log, TEXT("[VoiceEntity] Subsystems: Economy=%s Trade=%s Faction=%s Save=%s Mission=%s"),
		EconomySystem ? TEXT("FOUND") : TEXT("NULL"),
		TradeSystem ? TEXT("FOUND") : TEXT("NULL"),
		FactionSystem ? TEXT("FOUND") : TEXT("NULL"),
		SaveSystem ? TEXT("FOUND") : TEXT("NULL"),
		MissionSystem ? TEXT("FOUND") : TEXT("NULL"));
}

void AVoiceEntity::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// ─── Update status display with last response ────────────────
	if (!LastResponse.IsEmpty() && StatusDisplay)
	{
		StatusDisplay->SetText(FText::FromString(LastResponse));
	}

	// ─── Draw debug visualization when near player ───────────────
	DrawDebugVisualization(DeltaTime);
}

void AVoiceEntity::VoiceCommand(const FString& CommandText)
{
	if (bIsProcessing)
	{
		UE_LOG(LogTemp, Warning, TEXT("[VoiceEntity] Still processing previous command. Please wait..."));
		return;
	}

	bIsProcessing = true;
	UE_LOG(LogTemp, Log, TEXT("[VoiceEntity] Received voice command: %s"), *CommandText);

	// Audio cue: listening/processing has started (Phase 3 feedback).
	if (VoiceStartSound)
	{
		UGameplayStatics::PlaySoundAtLocation(GetWorld(), VoiceStartSound, GetActorLocation());
	}

	// ─── Parse the utterance using NLP parser ─────────────────────
	FVoiceAction Action;
	if (NlpParserInstance)
	{
		Action = NlpParserInstance->ParseUtterance(CommandText);
	}
	else
	{
		Action.Type = EVoiceActionType::Unknown;
		Action.QueryText = CommandText;
	}

	// ─── Execute the action ──────────────────────────────────────
	FVoiceActionResult Result = ExecuteVoiceAction(Action);

	if (Result.bSuccess)
	{
		UE_LOG(LogTemp, Log, TEXT("[VoiceEntity] Action succeeded: %s"), *Result.ResponseText);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("[VoiceEntity] Action failed: %s"), *Result.ResponseText);
	}

	// Audio cue: processing complete (Phase 3 feedback).
	if (VoiceEndSound)
	{
		UGameplayStatics::PlaySoundAtLocation(GetWorld(), VoiceEndSound, GetActorLocation());
	}
	bIsProcessing = false;
}

void AVoiceEntity::VoiceCommandFromAudio(const TArray<uint8>& AudioData)
{
	if (bIsProcessing)
	{
		UE_LOG(LogTemp, Warning, TEXT("[VoiceEntity] Still processing previous command. Please wait..."));
		return;
	}

	bIsProcessing = true;
	UE_LOG(LogTemp, Log, TEXT("[VoiceEntity] Received audio input (%d bytes)"), AudioData.Num());

	// ─── Process audio through STT engine (Phase 2) ──────────────
	FString TranscribedText;
	if (SttEngine && SttEngine->IsReady())
	{
		UE_LOG(LogTemp, Log, TEXT("[VoiceEntity] Processing audio through STT Engine"));
		TranscribedText = SttEngine->ProcessAudio(AudioData);
		
		UE_LOG(LogTemp, Log, TEXT("[VoiceEntity] Transcribed text: %s"), *TranscribedText);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("[VoiceEntity] STT Engine not ready - cannot process audio"));
		TranscribedText = TEXT("STT Engine not available");
	}

	// ─── Parse the transcribed text using NLP parser ──────────────
	FVoiceAction Action;
	if (NlpParserInstance)
	{
		Action = NlpParserInstance->ParseUtterance(TranscribedText);
	}
	else
	{
		Action.Type = EVoiceActionType::Unknown;
		Action.QueryText = TranscribedText;
	}

	// ─── Execute the action ──────────────────────────────────────
	FVoiceActionResult Result = ExecuteVoiceAction(Action);

	if (Result.bSuccess)
	{
		UE_LOG(LogTemp, Log, TEXT("[VoiceEntity] Audio command succeeded: %s"), *Result.ResponseText);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("[VoiceEntity] Audio command failed: %s"), *Result.ResponseText);
	}

	bIsProcessing = false;
}

FVoiceActionResult AVoiceEntity::ExecuteVoiceAction(const FVoiceAction& Action)
{
	FVoiceActionResult Result;
	Result.bSuccess = false;
	Result.ResponseText = TEXT("Unknown action.");

	switch (Action.Type)
	{
	case EVoiceActionType::SpawnActor:
		Result = ExecuteSpawn(Action);
		break;

	case EVoiceActionType::DeleteActor:
		Result = ExecuteDelete(Action);
		break;

	case EVoiceActionType::EconomyBuy:
		Result = ExecuteEconomyBuy(Action);
		break;

	case EVoiceActionType::EconomySell:
		Result = ExecuteEconomySell(Action);
		break;

	case EVoiceActionType::SaveGame:
		Result = ExecuteSaveGame();
		break;

	case EVoiceActionType::LoadGame:
		Result = ExecuteLoadGame();
		break;

	case EVoiceActionType::MissionAccept:
		Result = ExecuteMissionAccept();
		break;

	case EVoiceActionType::QueryWorld:
		Result = ExecuteQueryWorld(Action);
		break;

	case EVoiceActionType::ListActors:
		Result = ExecuteListActors();
		break;

	default:
		Result.ResponseText = TEXT("I didn't understand that command. Try 'spawn a rock' or 'buy titanium'.");
		break;
	}

	if (Result.bSuccess)
	{
		RespondToPlayer(Result.ResponseText, Result.DetailLog);
	}

	return Result;
}

void AVoiceEntity::VoiceStatus()
{
	FString Status = TEXT("Voice Entity Status:");
	Status += FString::Printf(TEXT("\n  NLP Parser: %s"), NlpParserInstance ? TEXT("OK") : TEXT("NULL"));
	Status += FString::Printf(TEXT("\n  STT Engine: %s"), (SttEngine && SttEngine->IsReady()) ? TEXT("OK") : TEXT("NULL"));
	Status += FString::Printf(TEXT("\n  Economy: %s"), EconomySystem ? TEXT("OK") : TEXT("NULL"));
	Status += FString::Printf(TEXT("\n  Trade: %s"), TradeSystem ? TEXT("OK") : TEXT("NULL"));
	Status += FString::Printf(TEXT("\n  Save: %s"), SaveSystem ? TEXT("OK") : TEXT("NULL"));
	Status += FString::Printf(TEXT("\n  Mission: %s"), MissionSystem ? TEXT("OK") : TEXT("NULL"));

	UE_LOG(LogTemp, Log, TEXT("%s"), *Status);

	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (PC)
	{
		PC->ClientMessage(*Status, FName(TEXT("VoiceEntity")), 5.0f);
	}
}

FVoiceActionResult AVoiceEntity::ExecuteSpawn(const FVoiceAction& Action)
{
	FVoiceActionResult Result;
	Result.bSuccess = false;

	AActor* PlayerPawn = GetPlayerPawn();
	if (!PlayerPawn)
	{
		Result.ResponseText = TEXT("I can't find the player to spawn near.");
		return Result;
	}

	FVector SpawnLocation = PlayerPawn->GetActorLocation() + FVector(0.0f, 0.0f, 100.0f);
	AActor* SpawnedActor = SpawnActorAtLocation(Action.Target, SpawnLocation);

	if (SpawnedActor)
	{
		Result.bSuccess = true;
		Result.ResponseText = FString::Printf(TEXT("Spawned %s at your location."), *Action.Target);
		Result.DetailLog = FString::Printf(TEXT("[VoiceEntity] Spawned actor: %s"), *Action.Target);
	}
	else
	{
		Result.ResponseText = TEXT("Could not spawn that object.");
	}

	return Result;
}

FVoiceActionResult AVoiceEntity::ExecuteDelete(const FVoiceAction& Action)
{
	FVoiceActionResult Result;
	Result.bSuccess = false;

	AActor* PlayerPawn = GetPlayerPawn();
	if (!PlayerPawn)
	{
		Result.ResponseText = TEXT("I can't find the player to delete near.");
		return Result;
	}

	FVector DeleteLocation = PlayerPawn->GetActorLocation() + FVector(0.0f, 0.0f, 100.0f);
	AActor* TargetActor = FindActorNearLocation(Action.Target, DeleteLocation);

	if (TargetActor)
	{
		GetWorld()->DestroyActor(TargetActor);
		Result.bSuccess = true;
		Result.ResponseText = FString::Printf(TEXT("Deleted %s."), *Action.Target);
		Result.DetailLog = FString::Printf(TEXT("[VoiceEntity] Deleted actor: %s"), *Action.Target);
	}
	else
	{
		Result.ResponseText = TEXT("Could not find that object to delete.");
	}

	return Result;
}

FVoiceActionResult AVoiceEntity::ExecuteEconomyBuy(const FVoiceAction& Action)
{
	FVoiceActionResult Result;
	Result.bSuccess = false;

	if (!TradeSystem || !EconomySystem)
	{
		Result.ResponseText = TEXT("Economy system not available.");
		return Result;
	}

	int32 Quantity = Action.Quantity > 0 ? Action.Quantity : 1;
	FString Commodity = Action.Target.IsEmpty() ? TEXT("Titanium") : Action.Target;

	// TODO: Call actual economy/trade logic
	Result.bSuccess = true;
	Result.ResponseText = FString::Printf(TEXT("Bought %d x %s."), Quantity, *Commodity);
	Result.DetailLog = FString::Printf(TEXT("[VoiceEntity] Economy buy: %d x %s"), Quantity, *Commodity);

	return Result;
}

FVoiceActionResult AVoiceEntity::ExecuteEconomySell(const FVoiceAction& Action)
{
	FVoiceActionResult Result;
	Result.bSuccess = false;

	if (!TradeSystem || !EconomySystem)
	{
		Result.ResponseText = TEXT("Economy system not available.");
		return Result;
	}

	int32 Quantity = Action.Quantity > 0 ? Action.Quantity : 1;
	FString Commodity = Action.Target.IsEmpty() ? TEXT("Titanium") : Action.Target;

	// TODO: Call actual economy/trade logic
	Result.bSuccess = true;
	Result.ResponseText = FString::Printf(TEXT("Sold %d x %s."), Quantity, *Commodity);
	Result.DetailLog = FString::Printf(TEXT("[VoiceEntity] Economy sell: %d x %s"), Quantity, *Commodity);

	return Result;
}

FVoiceActionResult AVoiceEntity::ExecuteEconomyStatus()
{
	FVoiceActionResult Result;
	Result.bSuccess = false;

	if (!EconomySystem)
	{
		Result.ResponseText = TEXT("Economy system not available.");
		return Result;
	}

	// TODO: Query actual economy status
	Result.bSuccess = true;
	Result.ResponseText = TEXT("Checking your economy status...");
	Result.DetailLog = TEXT("[VoiceEntity] Economy status query");

	return Result;
}

FVoiceActionResult AVoiceEntity::ExecuteSaveGame()
{
	FVoiceActionResult Result;
	Result.bSuccess = false;

	if (!SaveSystem)
	{
		Result.ResponseText = TEXT("Save system not available.");
		return Result;
	}

	// TODO: Call actual save logic
	Result.bSuccess = true;
	Result.ResponseText = TEXT("Game saved successfully.");
	Result.DetailLog = TEXT("[VoiceEntity] Game saved");

	return Result;
}

FVoiceActionResult AVoiceEntity::ExecuteLoadGame()
{
	FVoiceActionResult Result;
	Result.bSuccess = false;

	if (!SaveSystem)
	{
		Result.ResponseText = TEXT("Save system not available.");
		return Result;
	}

	// TODO: Call actual load logic
	Result.bSuccess = true;
	Result.ResponseText = TEXT("Game loaded from last save.");
	Result.DetailLog = TEXT("[VoiceEntity] Game loaded");

	return Result;
}

FVoiceActionResult AVoiceEntity::ExecuteMissionAccept()
{
	FVoiceActionResult Result;
	Result.bSuccess = false;

	if (!MissionSystem)
	{
		Result.ResponseText = TEXT("Mission system not available.");
		return Result;
	}

	// TODO: Call actual mission logic
	Result.bSuccess = true;
	Result.ResponseText = TEXT("Mission accepted: Deliver 500 Titanium to Orbital_Hub_7.");
	Result.DetailLog = TEXT("[VoiceEntity] Mission Delivery_Titanium_Batch_1 accepted");

	return Result;
}

FVoiceActionResult AVoiceEntity::ExecuteQueryWorld(const FVoiceAction& Action)
{
	FVoiceActionResult Result;
	AActor* PlayerPawn = GetPlayerPawn();
	if (!PlayerPawn)
	{
		Result.bSuccess = false;
		Result.ResponseText = TEXT("I can't find the player.");
		return Result;
	}

	FVector Location = PlayerPawn->GetActorLocation();
	FString QueryResponse = FString::Printf(
		TEXT("You are at position (%.0f, %.0f, %.0f)."),
		Location.X, Location.Y, Location.Z);

	Result.bSuccess = true;
	Result.ResponseText = QueryResponse;
	Result.DetailLog = FString::Printf(TEXT("[VoiceEntity] Player query - Position: (%.0f, %.0f, %.0f)"),
		Location.X, Location.Y, Location.Z);

	return Result;
}

FVoiceActionResult AVoiceEntity::ExecuteListActors()
{
	FVoiceActionResult Result;
	int32 ActorCount = 0;
	
	// Iterate through all actors in the world
	TArray<AActor*> AllActors;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), AActor::StaticClass(), AllActors);
	for (AActor* Actor : AllActors)
	{
		if (Actor && Actor != GetPlayerPawn())
		{
			ActorCount++;
		}
	}

	FString ListResponse = FString::Printf(
		TEXT("There are %d actors in this level."), ActorCount);

	Result.bSuccess = true;
	Result.ResponseText = ListResponse;
	Result.DetailLog = FString::Printf(TEXT("[VoiceEntity] Listed %d actors"), ActorCount);

	return Result;
}

AActor* AVoiceEntity::GetPlayerPawn() const
{
	// Get the first player controller and return its pawn
	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (PC)
	{
		return PC->GetPawn();
	}

	return nullptr;
}

AActor* AVoiceEntity::SpawnActorAtLocation(const FString& ActorClassPath, const FVector& Location)
{
	FString FullPath = TEXT("/Game/");
	if (!ActorClassPath.StartsWith(TEXT("/")))
	{
		FullPath += ActorClassPath;
	}
	else
	{
		FullPath = ActorClassPath;
	}

	UObject* Asset = FindObject<UObject>(nullptr, *FullPath);
	if (!Asset)
	{
		UE_LOG(LogTemp, Warning, TEXT("[VoiceEntity] Could not find asset: %s"), *FullPath);
		return nullptr;
	}

	FActorSpawnParameters SpawnParams;

	if (Asset->IsA<UStaticMesh>())
	{
		UStaticMesh* Mesh = Cast<UStaticMesh>(Asset);
		if (!Mesh) return nullptr;

		FTransform SpawnTransform(FRotator::ZeroRotator, Location, FVector(1.0f));
		AActor* SpawnedActor = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), SpawnTransform, SpawnParams);

		if (SpawnedActor)
		{
			UStaticMeshComponent* MeshComp = NewObject<UStaticMeshComponent>(SpawnedActor);
			MeshComp->SetStaticMesh(Mesh);
			MeshComp->SetupAttachment(SpawnedActor->GetRootComponent());
			MeshComp->SetWorldLocation(Location);
			SpawnedActor->AddInstanceComponent(MeshComp);
			SpawnedActor->SetActorLocation(Location);

			UE_LOG(LogTemp, Log, TEXT("[VoiceEntity] Spawned mesh actor at (%.0f, %.0f, %.0f)"),
				Location.X, Location.Y, Location.Z);
		}

		return SpawnedActor;
	}

	return nullptr;
}

AActor* AVoiceEntity::FindActorNearLocation(const FString& ActorName, const FVector& Location)
{
	TArray<AActor*> AllActors;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), AActor::StaticClass(), AllActors);
	for (AActor* Actor : AllActors)
	{
		if (Actor && Actor->GetName().Contains(*ActorName))
		{
			FVector ActorLoc = Actor->GetActorLocation();
			float Dist = FVector::Dist(Location, ActorLoc);
			if (Dist < 200.0f)
			{
				return Actor;
			}
		}
	}

	return nullptr;
}

void AVoiceEntity::DrawDebugVisualization(float DeltaTime)
{
	AActor* PlayerPawn = GetPlayerPawn();
	if (!PlayerPawn) return;

	float Dist = FVector::Dist(GetActorLocation(), PlayerPawn->GetActorLocation());
	DebugVisualizationTimer += DeltaTime;

	// Only draw debug when player is near (< 800 units)
	if (Dist < DEBUG_VISUALIZATION_RANGE)
	{
		FString DebugText = FString::Printf(TEXT("Voice Entity Active\nDistance: %.0f"), Dist);
		DrawDebugString(GetWorld(), GetActorLocation(), DebugText, nullptr, FColor::Green, 0.0f, true);
	}
}

void AVoiceEntity::RespondToPlayer(const FString& ResponseText, const FString& DetailLog)
{
	LastResponse = ResponseText;

	if (!DetailLog.IsEmpty())
	{
		UE_LOG(LogTemp, Log, TEXT("%s"), *DetailLog);
	}

	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (PC)
	{
		PC->ClientMessage(*ResponseText, FName(TEXT("VoiceEntity")), 2.0f);
	}
}
