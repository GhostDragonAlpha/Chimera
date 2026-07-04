// Copyright 2026 Chimera Project. All Rights Reserved.

#include "WID_TradeUI.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"

void UWID_TradeUI::NativeConstruct()
{
	Super::NativeConstruct();

	if (ConfirmTradeButton)
	{
		ConfirmTradeButton->OnClicked.AddDynamic(this, &UWID_TradeUI::OnConfirmTrade);
	}

	if (CancelTradeButton)
	{
		CancelTradeButton->OnClicked.AddDynamic(this, &UWID_TradeUI::OnCancelTrade);
	}
}

void UWID_TradeUI::SetTitleText(const FText& TitleText)
{
	if (TitleTextBlock)
	{
		TitleTextBlock->SetText(TitleText);
	}
}

void UWID_TradeUI::SetPlayerItemsList(const TArray<FString>& Items)
{
	// In a full implementation, this would populate the PlayerItemsListView with the provided items
	UE_LOG(LogTemp, Log, TEXT("Setting player items list with %d items"), Items.Num());
}

void UWID_TradeUI::SetNPCItemsList(const TArray<FString>& Items)
{
	// In a full implementation, this would populate the NPCItemsListView with the provided items
	UE_LOG(LogTemp, Log, TEXT("Setting NPC items list with %d items"), Items.Num());
}

void UWID_TradeUI::ShowTradeUI()
{
	if (UUserWidget* Widget = Cast<UUserWidget>(this))
	{
		Widget->AddToViewport();
	}
}

void UWID_TradeUI::HideTradeUI()
{
	if (UUserWidget* Widget = Cast<UUserWidget>(this))
	{
		Widget->RemoveFromParent();
	}
}

void UWID_TradeUI::OnConfirmTrade()
{
	// In a full implementation, this would handle the trade confirmation logic
	UE_LOG(LogTemp, Log, TEXT("Trade confirmed"));
	
	// Hide the UI after confirming
	HideTradeUI();
}

void UWID_TradeUI::OnCancelTrade()
{
	// In a full implementation, this would handle the trade cancellation logic
	UE_LOG(LogTemp, Log, TEXT("Trade cancelled"));
	
	// Hide the UI after cancelling
	HideTradeUI();
}
