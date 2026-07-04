// Copyright 2026 Chimera Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "WID_TradeUI.generated.h"

class UButton;
class UTextBlock;
class UListViewBase;

UCLASS()
class CHIMERA_API UWID_TradeUI : public UUserWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeConstruct() override;

public:
	/** Set the title text of the trade UI */
	UFUNCTION(BlueprintCallable, Category="Trade|UI")
	void SetTitleText(const FText& TitleText);

	/** Set player items list */
	UFUNCTION(BlueprintCallable, Category="Trade|UI")
	void SetPlayerItemsList(const TArray<FString>& Items);

	/** Set NPC items list */
	UFUNCTION(BlueprintCallable, Category="Trade|UI")
	void SetNPCItemsList(const TArray<FString>& Items);

	/** Show the trade UI */
	UFUNCTION(BlueprintCallable, Category="Trade|UI")
	void ShowTradeUI();

	/** Hide the trade UI */
	UFUNCTION(BlueprintCallable, Category="Trade|UI")
	void HideTradeUI();

	/** Confirm the trade exchange */
	UFUNCTION(BlueprintCallable, Category="Trade|UI")
	void OnConfirmTrade();

	/** Cancel the trade exchange */
	UFUNCTION(BlueprintCallable, Category="Trade|UI")
	void OnCancelTrade();

private:
	/** Title text block */
	UPROPERTY(meta=(BindWidget))
	UTextBlock* TitleTextBlock;

	/** Player items list view */
	UPROPERTY(meta=(BindWidget))
	UListViewBase* PlayerItemsListView;

	/** NPC items list view */
	UPROPERTY(meta=(BindWidget))
	UListViewBase* NPCItemsListView;

	/** Confirm trade button */
	UPROPERTY(meta=(BindWidget))
	UButton* ConfirmTradeButton;

	/** Cancel trade button */
	UPROPERTY(meta=(BindWidget))
	UButton* CancelTradeButton;
};