// Copyright 2026 Chimera Project. All Rights Reserved.
#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "WID_O2HUD.generated.h"

class USuitLifeSupportComponent;

/**
 * O2 HUD Widget — displays the suit's life-support readouts: O2, Battery, Dust Clog.
 * Updates each frame by reading from the player pawn's USuitLifeSupportComponent.
 * Shows visual gauges and percentage text. Alerts on low O2.
 *
 * Self-contained: finds the component at runtime, no Blueprint wiring needed.
 * Durable loop-built code under UI/ — safe to hand-edit and extend.
 */
UCLASS()
class CHIMERA_API UWID_O2HUD : public UUserWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

public:
	/** Add this widget to the viewport (called by DemoPlayerController). */
	UFUNCTION(BlueprintCallable, Category = "O2HUD")
	void ShowO2HUD();

	/** Remove this widget from the viewport. */
	UFUNCTION(BlueprintCallable, Category = "O2HUD")
	void HideO2HUD();

protected:
	/** Cached reference to the player pawn's suit component — fetched once at construct. */
	UPROPERTY()
	class USuitLifeSupportComponent* SuitComponent;

	// === Progress bars (visual gauges) ===
	UPROPERTY(meta = (BindWidget))
	class UProgressBar* O2ProgressBar;

	UPROPERTY(meta = (BindWidget))
	class UProgressBar* BatteryProgressBar;

	UPROPERTY(meta = (BindWidget))
	class UProgressBar* DustClogProgressBar;

	// === Text displays (percentage + status) ===
	UPROPERTY(meta = (BindWidget))
	class UTextBlock* O2PercentText;

	UPROPERTY(meta = (BindWidget))
	class UTextBlock* BatteryPercentText;

	UPROPERTY(meta = (BindWidget))
	class UTextBlock* DustClogPercentText;

	UPROPERTY(meta = (BindWidget))
	class UTextBlock* AlertText;

	/** Attempt to find the suit component on the player pawn. Called once at construct. */
	void FindSuitComponent();

	/** Update all gauge visuals and text from the current suit state. */
	void UpdateHUDDisplay();

	/** Update the low-O2 alert message. */
	void UpdateAlertState();

	/** Convert a 0..1 fraction to a percentage string. */
	FString FormatPercentage(float Fraction) const;

	/** Last recorded low-O2 state — used to detect edge transitions for alerts. */
	bool bWasLowO2;
};
