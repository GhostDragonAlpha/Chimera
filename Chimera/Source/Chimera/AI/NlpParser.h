// Copyright 2026 Chimera Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "VoiceCommandStructs.h"
#include "NlpParser.generated.h"

/**
 * Natural Language Parser for voice commands.
 * 
 * Converts natural language utterances into structured FVoiceAction objects.
 * Uses pattern matching and keyword extraction — no external dependencies needed.
 * 
 * Examples:
 *   "spawn a rock here" → SpawnActor(SM_Rock, player_location)
 *   "make the sky darker" → ModifyProperty(SkyBrightness, 0.3)
 *   "buy 100 titanium" → EconomyBuy(Titanium, 100)
 *   "what can I do?" → QueryWorld("list available commands")
 */
UCLASS(BlueprintType, meta = (BlueprintThreadSafe))
class CHIMERA_API UNlpParser : public UObject
{
	GENERATED_BODY()

public:
	UNlpParser() {}

	/**
	 * Parse a natural language utterance into a structured voice action.
	 * @param Utterance The raw text from speech-to-text engine
	 * @return FVoiceAction with Type, Target, Location, etc. filled in
	 */
	UFUNCTION(BlueprintCallable, Category = "Chimera|NLP")
	FVoiceAction ParseUtterance(const FString& Utterance);

	/**
	 * Check if an utterance matches a known command pattern.
	 * @param Utterance The raw text to check
	 * @return True if the utterance is recognized as a valid command
	 */
	UFUNCTION(BlueprintCallable, Category = "Chimera|NLP", meta = (DeprecatedFunction))
	bool IsRecognizedCommand(const FString& Utterance);

private:
	/** Extract numeric values from utterance (e.g., "100 titanium" → 100) */

	int32 ExtractNumber(const FString& Utterance) const;

	/** Extract actor type keywords (rock, tree, building, etc.) */
	FString ExtractActorType(const FString& Utterance) const;

	/** Extract commodity names from utterance */
	FString ExtractCommodityName(const FString& Utterance) const;

	/** Map natural language property names to UE property paths */
	FName ResolvePropertyName(const FString& PropertyName) const;

	/** Known command patterns for matching */
	struct FCommandPattern
	{
		EVoiceActionType ActionType;
		TArray<FString> Keywords;  // Words that trigger this pattern
		FString ResponseTemplate;  // Template for response text
	};

	TArray<FCommandPattern> CommandPatterns;

	/** Initialize command patterns on first use */
	void EnsurePatternsLoaded();
};
