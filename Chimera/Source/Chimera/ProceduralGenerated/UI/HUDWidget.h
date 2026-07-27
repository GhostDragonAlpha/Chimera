// Copyright 2026 Chimera Project. All Rights Reserved.
#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "HUDWidget.generated.h"

class UTextBlock;
class UScrollBox;
class UVerticalBox;

/**
 * Core HUD widget that displays credits, inventory count, active missions,
 * and faction standing — the player's persistent status bar.
 */
UCLASS(Blueprintable, BlueprintType)
class CHIMERA_API UHUDWidget : public UUserWidget
{
    GENERATED_BODY()

protected:
    virtual void NativeConstruct() override;

public:
    /** Update credits display */
    UFUNCTION(BlueprintCallable, Category = "HUD")
    void SetCredits(float Credits);

    /** Update inventory count */
    UFUNCTION(BlueprintCallable, Category = "HUD")
    void SetInventoryCount(int32 Count);

    /** Add a mission to the tracker list */
    UFUNCTION(BlueprintCallable, Category = "HUD")
    void AddMission(FString MissionName, FString ObjectiveText);

    /** Remove a completed mission from tracker */
    UFUNCTION(BlueprintCallable, Category = "HUD")
    void RemoveMission(FString MissionID);

    /** Update faction standing display */
    UFUNCTION(BlueprintCallable, Category = "HUD")
    void SetFactionStanding(FName FactionID, float Standing);

    /** Show a floating message (e.g., trade confirmation) */
    UFUNCTION(BlueprintCallable, Category = "HUD|Messages")
    void ShowMessage(FString MessageText, float Duration = 3.0f);

    /** Clear all messages */
    UFUNCTION(BlueprintCallable, Category = "HUD|Messages")
    void ClearMessages();

    /** Set the current loop number display */
    UFUNCTION(BlueprintCallable, Category = "HUD")
    void SetLoopNumber(int32 LoopNum);

protected:
    // Slate widgets (bound in Blueprint at runtime)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (BindWidget))
    class UTextBlock* CreditsText;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (BindWidget))
    class UTextBlock* InventoryText;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (BindWidget))
    class UTextBlock* LoopNumberText;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (BindWidget))
    class UScrollBox* MissionList;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (BindWidget))
    class UVerticalBox* MessageStack;

    /** Tracks mission entry widgets by key (the MissionName passed to AddMission)
     *  so RemoveMission can remove exactly one row from MissionList. */
    UPROPERTY()
    TMap<FString, UTextBlock*> MissionEntries;

    /** Internal: create a message widget and add to stack */
    void AddMessageToStack(FString Text);
};
