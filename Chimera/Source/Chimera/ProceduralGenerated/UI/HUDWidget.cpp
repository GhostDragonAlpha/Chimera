// Copyright 2026 Chimera Project. All Rights Reserved.

#include "HUDWidget.h"
#include "Components/TextBlock.h"
#include "Components/ScrollBox.h"
#include "Components/VerticalBox.h"
#include "Engine/World.h"
#include "TimerManager.h"

void UHUDWidget::NativeConstruct()
{
    Super::NativeConstruct();

    // BindWidget pointers are valid from here on. Seed the persistent status
    // fields with sane defaults so the bar reads correctly before any gameplay
    // event pushes real values.
    SetCredits(0.0f);
    SetInventoryCount(0);
    SetLoopNumber(0);
}

void UHUDWidget::SetCredits(float Credits)
{
    if (CreditsText)
    {
        CreditsText->SetText(FText::AsNumber(FMath::RoundToInt(Credits)));
    }
}

void UHUDWidget::SetInventoryCount(int32 Count)
{
    if (InventoryText)
    {
        InventoryText->SetText(FText::AsNumber(Count));
    }
}

void UHUDWidget::AddMission(FString MissionName, FString ObjectiveText)
{
    if (!MissionList)
    {
        return;
    }

    const FString Line = FString::Printf(TEXT("%s: %s"), *MissionName, *ObjectiveText);

    // If a mission with this key already exists, update its objective in place
    // rather than adding a duplicate row.
    if (UTextBlock** Existing = MissionEntries.Find(MissionName))
    {
        if (*Existing)
        {
            (*Existing)->SetText(FText::FromString(Line));
            return;
        }
    }

    UTextBlock* Entry = NewObject<UTextBlock>(this);
    if (!Entry)
    {
        return;
    }
    Entry->SetText(FText::FromString(Line));
    Entry->SetColorAndOpacity(FSlateColor(FLinearColor::White));
    MissionList->AddChild(Entry);
    MissionEntries.Add(MissionName, Entry);
}

void UHUDWidget::RemoveMission(FString MissionID)
{
    // MissionID is the same string passed as MissionName to AddMission.
    if (UTextBlock** Found = MissionEntries.Find(MissionID))
    {
        if (*Found)
        {
            (*Found)->RemoveFromParent();
        }
    }
    MissionEntries.Remove(MissionID);
}

void UHUDWidget::SetFactionStanding(FName FactionID, float Standing)
{
    // Faction standing is surfaced as a transient message until a dedicated
    // faction panel exists; keeps the value observable in-game and in logs.
    UE_LOG(LogTemp, Log, TEXT("[HUD] Faction %s standing: %.1f"), *FactionID.ToString(), Standing);
    ShowMessage(FString::Printf(TEXT("%s standing: %.0f"), *FactionID.ToString(), Standing), 2.0f);
}

void UHUDWidget::ShowMessage(FString MessageText, float Duration)
{
    AddMessageToStack(MessageText);

    // Auto-clear after Duration seconds. A single shared timer clears the whole
    // stack, which is adequate for the current transient-toast use.
    if (Duration > 0.0f)
    {
        if (UWorld* World = GetWorld())
        {
            FTimerHandle Handle;
            World->GetTimerManager().SetTimer(Handle, this, &UHUDWidget::ClearMessages, Duration, false);
        }
    }
}

void UHUDWidget::ClearMessages()
{
    if (MessageStack)
    {
        MessageStack->ClearChildren();
    }
}

void UHUDWidget::SetLoopNumber(int32 LoopNum)
{
    if (LoopNumberText)
    {
        LoopNumberText->SetText(FText::FromString(FString::Printf(TEXT("Loop %d"), LoopNum)));
    }
}

void UHUDWidget::AddMessageToStack(FString Text)
{
    if (!MessageStack)
    {
        return;
    }

    UTextBlock* Message = NewObject<UTextBlock>(this);
    if (!Message)
    {
        return;
    }
    Message->SetText(FText::FromString(Text));
    Message->SetColorAndOpacity(FSlateColor(FLinearColor::White));
    MessageStack->AddChild(Message);
}
