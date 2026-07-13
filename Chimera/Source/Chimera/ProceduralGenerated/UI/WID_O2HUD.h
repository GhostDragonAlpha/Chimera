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
 * BUILDS ITS OWN WIDGET TREE IN C++ (P0 fix, 2026-07-13): this project cannot author
 * UMG Blueprint (WBP) assets, so the original meta=(BindWidget) properties bound to
 * nothing and CreateWidget<UWID_O2HUD>() rendered an empty widget (diagnosed GOTCHA —
 * design directive Section 1). NativeOnInitialized() now constructs a real widget tree
 * (CanvasPanel -> Border -> VerticalBox of gauge rows) via WidgetTree->ConstructWidget,
 * so the gauges render with zero Blueprint dependency.
 * Durable loop-built code under UI/ — safe to hand-edit and extend.
 */
UCLASS()
class CHIMERA_API UWID_O2HUD : public UUserWidget
{
	GENERATED_BODY()

protected:
	/** Guaranteed to run before this widget's first Slate representation is taken
	 *  (Initialize() already ensures WidgetTree is non-null for native-only UUserWidget
	 *  classes) — the correct, order-safe hook for programmatic UMG construction. */
	virtual void NativeOnInitialized() override;
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

	// === Progress bars (visual gauges) — built in C++ by BuildWidgetTree(), not
	// Blueprint-bound (no meta=BindWidget: there is no WBP asset to bind to). ===
	UPROPERTY()
	class UProgressBar* O2ProgressBar;

	UPROPERTY()
	class UProgressBar* BatteryProgressBar;

	UPROPERTY()
	class UProgressBar* DustClogProgressBar;

	// === Text displays (percentage + status) ===
	UPROPERTY()
	class UTextBlock* O2PercentText;

	UPROPERTY()
	class UTextBlock* BatteryPercentText;

	UPROPERTY()
	class UTextBlock* DustClogPercentText;

	UPROPERTY()
	class UTextBlock* AlertText;

	/** Construct the whole widget tree in C++ (root Canvas -> Border -> VerticalBox of
	 *  gauge rows) and assign the member pointers above. Called once from
	 *  NativeOnInitialized(), before this widget is ever painted. */
	void BuildWidgetTree();

	/** Helper: build one gauge row (label + progress bar + percent text) inside Parent. */
	class UProgressBar* BuildGaugeRow(class UVerticalBox* Parent, const FString& RowLabel,
		const FLinearColor& BarColor, class UTextBlock*& OutPercentText);

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
