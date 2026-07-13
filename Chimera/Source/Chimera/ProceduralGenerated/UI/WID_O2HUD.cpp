// Copyright 2026 Chimera Project. All Rights Reserved.
#include "WID_O2HUD.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "../Suit/SuitLifeSupportComponent.h"

void UWID_O2HUD::NativeConstruct()
{
	Super::NativeConstruct();

	bWasLowO2 = false;
	FindSuitComponent();

	// Seed display with sane defaults in case suit component is not found
	if (O2ProgressBar)      O2ProgressBar->SetPercent(0.0f);
	if (BatteryProgressBar) BatteryProgressBar->SetPercent(0.0f);
	if (DustClogProgressBar) DustClogProgressBar->SetPercent(0.0f);
	if (O2PercentText)      O2PercentText->SetText(FText::FromString(TEXT("O2: 0%")));
	if (BatteryPercentText) BatteryPercentText->SetText(FText::FromString(TEXT("BAT: 0%")));
	if (DustClogPercentText) DustClogPercentText->SetText(FText::FromString(TEXT("DUST: 0%")));
	if (AlertText)          AlertText->SetText(FText::FromString(TEXT("")));

	UE_LOG(LogTemp, Display, TEXT("[O2HUD] Widget constructed. Suit component %s."), SuitComponent ? TEXT("FOUND") : TEXT("NOT FOUND"));
}

void UWID_O2HUD::NativeDestruct()
{
	Super::NativeDestruct();
	SuitComponent = nullptr;
}

void UWID_O2HUD::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	// If we lost the suit component, try to find it again (e.g., after repossess)
	if (!SuitComponent)
	{
		FindSuitComponent();
	}

	UpdateHUDDisplay();
	UpdateAlertState();
}

void UWID_O2HUD::FindSuitComponent()
{
	SuitComponent = nullptr;

	// Get the owning player controller
	APlayerController* PC = GetOwningPlayer();
	if (!PC)
	{
		UE_LOG(LogTemp, Warning, TEXT("[O2HUD] No owning player controller"));
		return;
	}

	// Get the possessed pawn
	APawn* PlayerPawn = PC->GetPawn();
	if (!PlayerPawn)
	{
		UE_LOG(LogTemp, Warning, TEXT("[O2HUD] Player controller has no possessed pawn"));
		return;
	}

	// Try to find the suit component on the pawn
	SuitComponent = PlayerPawn->FindComponentByClass<USuitLifeSupportComponent>();
	if (!SuitComponent)
	{
		// Component doesn't exist — attach one (workaround to keep everything in UI/ footprint).
		// In the proper fix, DemoPlayerController should attach this, like it does for
		// PickupInteractionComponent, FootprintComponent, and ChimeraMovementComponent.
		UE_LOG(LogTemp, Warning, TEXT("[O2HUD] SuitLifeSupportComponent not found on %s — attaching new instance"), *GetNameSafe(PlayerPawn));

		SuitComponent = NewObject<USuitLifeSupportComponent>(PlayerPawn, TEXT("SuitLifeSupportComponent"));
		if (SuitComponent)
		{
			SuitComponent->RegisterComponent();
			UE_LOG(LogTemp, Display, TEXT("[O2HUD] SuitLifeSupportComponent attached to %s"), *GetNameSafe(PlayerPawn));
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("[O2HUD] Failed to create SuitLifeSupportComponent"));
		}
		return;
	}

	UE_LOG(LogTemp, Display, TEXT("[O2HUD] SuitLifeSupportComponent found on %s"), *GetNameSafe(PlayerPawn));
}

void UWID_O2HUD::UpdateHUDDisplay()
{
	if (!SuitComponent)
	{
		return;
	}

	// Read current suit state
	const float O2Frac = SuitComponent->GetO2Fraction();
	const float BatteryFrac = SuitComponent->GetBatteryFraction();
	const float DustFrac = SuitComponent->GetDustClogFraction();

	// Update progress bars
	if (O2ProgressBar)
	{
		O2ProgressBar->SetPercent(O2Frac);
	}
	if (BatteryProgressBar)
	{
		BatteryProgressBar->SetPercent(BatteryFrac);
	}
	if (DustClogProgressBar)
	{
		DustClogProgressBar->SetPercent(DustFrac);
	}

	// Update percentage text
	if (O2PercentText)
	{
		O2PercentText->SetText(FText::FromString(FString::Printf(TEXT("O2: %s"), *FormatPercentage(O2Frac))));
	}
	if (BatteryPercentText)
	{
		BatteryPercentText->SetText(FText::FromString(FString::Printf(TEXT("BAT: %s"), *FormatPercentage(BatteryFrac))));
	}
	if (DustClogPercentText)
	{
		DustClogPercentText->SetText(FText::FromString(FString::Printf(TEXT("DUST: %s"), *FormatPercentage(DustFrac))));
	}
}

void UWID_O2HUD::UpdateAlertState()
{
	if (!SuitComponent || !AlertText)
	{
		return;
	}

	const bool bIsLowO2 = SuitComponent->IsLowO2();
	const bool bIsDead = SuitComponent->IsDead();

	// Show death alert
	if (bIsDead)
	{
		AlertText->SetText(FText::FromString(TEXT("SUIT FAILURE — O2 DEPLETED")));
		AlertText->SetColorAndOpacity(FSlateColor(FLinearColor::Red));
	}
	// Show low-O2 warning
	else if (bIsLowO2)
	{
		AlertText->SetText(FText::FromString(TEXT("WARNING: Low O2")));
		AlertText->SetColorAndOpacity(FSlateColor(FLinearColor::Yellow));
	}
	// Clear alert
	else
	{
		AlertText->SetText(FText::FromString(TEXT("")));
	}

	// Log edge transitions (just once per change)
	if (bIsLowO2 != bWasLowO2)
	{
		bWasLowO2 = bIsLowO2;
		if (bIsLowO2)
		{
			UE_LOG(LogTemp, Warning, TEXT("[O2HUD] Low O2 ALARM triggered (%.1f%%)"), SuitComponent->GetO2Fraction() * 100.0f);
		}
		else
		{
			UE_LOG(LogTemp, Display, TEXT("[O2HUD] Low O2 ALARM cleared (%.1f%%)"), SuitComponent->GetO2Fraction() * 100.0f);
		}
	}
}

FString UWID_O2HUD::FormatPercentage(float Fraction) const
{
	const int32 Percent = FMath::RoundToInt(FMath::Clamp(Fraction, 0.0f, 1.0f) * 100.0f);
	return FString::Printf(TEXT("%d%%"), Percent);
}

void UWID_O2HUD::ShowO2HUD()
{
	AddToViewport();
	UE_LOG(LogTemp, Display, TEXT("[O2HUD] Widget added to viewport"));
}

void UWID_O2HUD::HideO2HUD()
{
	RemoveFromParent();
	UE_LOG(LogTemp, Display, TEXT("[O2HUD] Widget removed from viewport"));
}
