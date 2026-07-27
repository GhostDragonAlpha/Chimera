// Copyright 2026 Chimera Project. All Rights Reserved.
#pragma warning(disable: 5038)
#pragma warning(disable: 4996)
#include "WID_O2HUD.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Border.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "../Suit/SuitLifeSupportComponent.h"

void UWID_O2HUD::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	// Build the render tree exactly once, before this widget is ever taken/painted
	// (Initialize() — our caller's caller — already guarantees WidgetTree is non-null
	// for a native-only UUserWidget subclass like this one; see class comment).
	if (!O2ProgressBar)
	{
		BuildWidgetTree();
	}
}

UProgressBar* UWID_O2HUD::BuildGaugeRow(UVerticalBox* Parent, const FString& RowLabel,
	const FLinearColor& BarColor, UTextBlock*& OutPercentText)
{
	if (!Parent || !WidgetTree)
	{
		OutPercentText = nullptr;
		return nullptr;
	}

	const FName RowName(*FString::Printf(TEXT("O2HUD_%sRow"), *RowLabel));
	UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), RowName);

	// Label (e.g. "O2")
	UTextBlock* Label = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(),
		FName(*FString::Printf(TEXT("O2HUD_%sLabel"), *RowLabel)));
	Label->SetText(FText::FromString(RowLabel));
	Label->SetColorAndOpacity(FSlateColor(FLinearColor(0.85f, 0.9f, 0.9f, 1.0f)));
	{
		FSlateFontInfo F = Label->GetFont();
		F.Size = 14;
		Label->SetFont(F);
	}
	if (UHorizontalBoxSlot* LabelSlot = Row->AddChildToHorizontalBox(Label))
	{
		LabelSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
		LabelSlot->SetVerticalAlignment(VAlign_Center);
		LabelSlot->SetPadding(FMargin(0.0f, 0.0f, 8.0f, 0.0f));
	}

	// Gauge bar (fills remaining row width)
	UProgressBar* Bar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(),
		FName(*FString::Printf(TEXT("O2HUD_%sBar"), *RowLabel)));
	Bar->SetPercent(0.0f);
	Bar->SetFillColorAndOpacity(BarColor);
	if (UHorizontalBoxSlot* BarSlot = Row->AddChildToHorizontalBox(Bar))
	{
		BarSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		BarSlot->SetVerticalAlignment(VAlign_Center);
		BarSlot->SetPadding(FMargin(0.0f, 0.0f, 8.0f, 0.0f));
	}

	// Percent readout (e.g. "45%")
	UTextBlock* PercentText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(),
		FName(*FString::Printf(TEXT("O2HUD_%sPercent"), *RowLabel)));
	PercentText->SetText(FText::FromString(TEXT("0%")));
	PercentText->SetColorAndOpacity(FSlateColor(FLinearColor::White));
	if (UHorizontalBoxSlot* PercentSlot = Row->AddChildToHorizontalBox(PercentText))
	{
		PercentSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
		PercentSlot->SetVerticalAlignment(VAlign_Center);
	}

	if (UVerticalBoxSlot* RowSlot = Parent->AddChildToVerticalBox(Row))
	{
		RowSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 6.0f));
	}

	OutPercentText = PercentText;
	return Bar;
}

void UWID_O2HUD::BuildWidgetTree()
{
	if (!WidgetTree)
	{
		// Defensive: Initialize() already creates this for native-only UUserWidget
		// classes, but a null check costs nothing and protects against future
		// engine-version changes to that guarantee.
		WidgetTree = NewObject<UWidgetTree>(this, TEXT("WidgetTree"), RF_Transient);
	}

	// Root: a CanvasPanel so the gauge cluster can be anchored to a screen corner
	// (a "glance down at your wrist" HUD position) instead of stretching full-screen.
	UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("O2HUD_RootCanvas"));
	WidgetTree->RootWidget = Root;

	// Background panel — dark translucent card behind the gauges for legibility
	// against any world background (Law: reads as a suit HUD, not console text).
	UBorder* Background = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("O2HUD_Background"));
	Background->SetBrushColor(FLinearColor(0.02f, 0.05f, 0.05f, 0.55f));
	Background->SetPadding(FMargin(14.0f, 10.0f));

	if (UCanvasPanelSlot* BgSlot = Root->AddChildToCanvas(Background))
	{
		// Anchor bottom-left; Alignment(0,1) pins the widget's own bottom-left
		// corner to that anchor; Position is the margin offset from the corner.
		BgSlot->SetAnchors(FAnchors(0.0f, 1.0f, 0.0f, 1.0f));
		BgSlot->SetAlignment(FVector2D(0.0f, 1.0f));
		BgSlot->SetPosition(FVector2D(40.0f, -40.0f));
		BgSlot->SetSize(FVector2D(300.0f, 160.0f));
		BgSlot->SetAutoSize(false);
	}

	UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("O2HUD_Stack"));
	Background->SetContent(Stack);

	// Title
	UTextBlock* Title = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("O2HUD_Title"));
	Title->SetText(FText::FromString(TEXT("SUIT STATUS")));
	Title->SetColorAndOpacity(FSlateColor(FLinearColor(0.6f, 0.9f, 1.0f, 1.0f)));
	{
		FSlateFontInfo F = Title->GetFont();
		F.Size = 15;
		Title->SetFont(F);
	}
	if (UVerticalBoxSlot* TitleSlot = Stack->AddChildToVerticalBox(Title))
	{
		TitleSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 8.0f));
	}

	// Three gauge rows — cyan O2, amber battery, tan dust.
	O2ProgressBar = BuildGaugeRow(Stack, TEXT("O2"), FLinearColor(0.2f, 0.8f, 1.0f, 1.0f), O2PercentText);
	BatteryProgressBar = BuildGaugeRow(Stack, TEXT("BAT"), FLinearColor(1.0f, 0.85f, 0.1f, 1.0f), BatteryPercentText);
	DustClogProgressBar = BuildGaugeRow(Stack, TEXT("DUST"), FLinearColor(0.65f, 0.5f, 0.3f, 1.0f), DustClogPercentText);

	// Alert line (low-O2 / death warning)
	AlertText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("O2HUD_AlertText"));
	AlertText->SetText(FText::GetEmpty());
	{
		FSlateFontInfo F = AlertText->GetFont();
		F.Size = 16;
		AlertText->SetFont(F);
	}
	if (UVerticalBoxSlot* AlertSlot = Stack->AddChildToVerticalBox(AlertText))
	{
		AlertSlot->SetPadding(FMargin(0.0f, 6.0f, 0.0f, 0.0f));
		AlertSlot->SetHorizontalAlignment(HAlign_Center);
	}

	UE_LOG(LogTemp, Display, TEXT("[O2HUD] Widget tree built in C++ (no WBP asset): CanvasPanel->Border->VerticalBox, 3 gauge rows + alert line"));
}

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
