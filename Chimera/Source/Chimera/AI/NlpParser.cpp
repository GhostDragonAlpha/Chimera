// Copyright 2026 Chimera Project. All Rights Reserved.

#include "NlpParser.h"
#include "VoiceCommandStructs.h"

void UNlpParser::EnsurePatternsLoaded()
{
	if (CommandPatterns.Num() > 0) return; // Already loaded

	// ─── Spawn patterns ──────────────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::SpawnActor;
		Pattern.Keywords = {TEXT("spawn"), TEXT("create"), TEXT("add"), TEXT("put"), TEXT("generate")};
		Pattern.ResponseTemplate = TEXT("Spawned {Target} at your location.");
		CommandPatterns.Add(Pattern);
	}

	// ─── Delete patterns ─────────────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::DeleteActor;
		Pattern.Keywords = {TEXT("delete"), TEXT("remove"), TEXT("destroy"), TEXT("get rid of")};
		Pattern.ResponseTemplate = TEXT("Deleted {Target}.");
		CommandPatterns.Add(Pattern);
	}

	// ─── Economy buy patterns ────────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::EconomyBuy;
		Pattern.Keywords = {TEXT("buy"), TEXT("purchase"), TEXT("get"), TEXT("acquire")};
		Pattern.ResponseTemplate = TEXT("Bought {Quantity}x {Target}.");
		CommandPatterns.Add(Pattern);
	}

	// ─── Economy sell patterns ───────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::EconomySell;
		Pattern.Keywords = {TEXT("sell"), TEXT("trade"), TEXT("exchange")};
		Pattern.ResponseTemplate = TEXT("Sold {Quantity}x {Target}.");
		CommandPatterns.Add(Pattern);
	}

	// ─── Economy status patterns ─────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::EconomyStatus;
		Pattern.Keywords = {TEXT("status"), TEXT("balance"), TEXT("credits"), TEXT("money"), TEXT("wealth")};
		Pattern.ResponseTemplate = TEXT("Checking your economy status...");
		CommandPatterns.Add(Pattern);
	}

	// ─── Save/Load patterns ──────────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::SaveGame;
		Pattern.Keywords = {TEXT("save"), TEXT("snapshot"), TEXT("checkpoint")};
		Pattern.ResponseTemplate = TEXT("Game saved.");
		CommandPatterns.Add(Pattern);
	}

	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::LoadGame;
		Pattern.Keywords = {TEXT("load"), TEXT("restore"), TEXT("reload")};
		Pattern.ResponseTemplate = TEXT("Game loaded from last save.");
		CommandPatterns.Add(Pattern);
	}

	// ─── Mission patterns ────────────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::MissionAccept;
		Pattern.Keywords = {TEXT("accept"), TEXT("take"), TEXT("start"), TEXT("begin")};
		Pattern.ResponseTemplate = TEXT("Mission accepted.");
		CommandPatterns.Add(Pattern);
	}

	// ─── Property modification patterns ──────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::ModifyProperty;
		Pattern.Keywords = {TEXT("make"), TEXT("set"), TEXT("change"), TEXT("adjust")};
		Pattern.ResponseTemplate = TEXT("Property modified.");
		CommandPatterns.Add(Pattern);
	}

	// ─── Query patterns ──────────────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::QueryWorld;
		Pattern.Keywords = {TEXT("what"), TEXT("where"), TEXT("how"), TEXT("tell me"), TEXT("show me")};
		Pattern.ResponseTemplate = TEXT("Processing your query...");
		CommandPatterns.Add(Pattern);
	}

	// ─── List actors patterns ────────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::ListActors;
		Pattern.Keywords = {TEXT("list"), TEXT("show all"), TEXT("count"), TEXT("actors"), TEXT("objects")};
		Pattern.ResponseTemplate = TEXT("Listing world actors...");
		CommandPatterns.Add(Pattern);
	}

	// ─── Gravity patterns ────────────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::SetGravity;
		Pattern.Keywords = {TEXT("gravity"), TEXT("weight"), TEXT("float")};
		Pattern.ResponseTemplate = TEXT("Gravity adjusted.");
		CommandPatterns.Add(Pattern);
	}

	// ─── Time dilation patterns ──────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::SetTimeDilation;
		Pattern.Keywords = {TEXT("slow"), TEXT("fast"), TEXT("time"), TEXT("speed")};
		Pattern.ResponseTemplate = TEXT("Time dilation adjusted.");
		CommandPatterns.Add(Pattern);
	}

	// ─── Move patterns ───────────────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::MoveActor;
		Pattern.Keywords = {TEXT("move"), TEXT("go to"), TEXT("teleport"), TEXT("walk")};
		Pattern.ResponseTemplate = TEXT("Moving...");
		CommandPatterns.Add(Pattern);
	}

	// ─── Rotate patterns ─────────────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::RotateActor;
		Pattern.Keywords = {TEXT("rotate"), TEXT("turn"), TEXT("spin")};
		Pattern.ResponseTemplate = TEXT("Rotation applied.");
		CommandPatterns.Add(Pattern);
	}

	// ─── Scale patterns ──────────────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::ScaleActor;
		Pattern.Keywords = {TEXT("scale"), TEXT("size"), TEXT("bigger"), TEXT("smaller")};
		Pattern.ResponseTemplate = TEXT("Scale adjusted.");
		CommandPatterns.Add(Pattern);
	}

	// ─── Query player patterns ───────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::QueryPlayer;
		Pattern.Keywords = {TEXT("my position"), TEXT("where am i"), TEXT("am I here")};
		Pattern.ResponseTemplate = TEXT("Retrieving your position...");
		CommandPatterns.Add(Pattern);
	}

	// ─── Query property patterns ─────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::QueryProperty;
		Pattern.Keywords = {TEXT("what is"), TEXT("check"), TEXT("read"), TEXT("value of")};
		Pattern.ResponseTemplate = TEXT("Reading property...");
		CommandPatterns.Add(Pattern);
	}

	// ─── Mission status patterns ─────────────────────────────────────
	{
		FCommandPattern Pattern;
		Pattern.ActionType = EVoiceActionType::MissionStatus;
		Pattern.Keywords = {TEXT("mission"), TEXT("objective"), TEXT("task"), TEXT("progress")};
		Pattern.ResponseTemplate = TEXT("Checking mission status...");
		CommandPatterns.Add(Pattern);
	}

	UE_LOG(LogTemp, Log, TEXT("[NLP] Loaded %d command patterns."), CommandPatterns.Num());
}

FVoiceAction UNlpParser::ParseUtterance(const FString& Utterance)
{
	EnsurePatternsLoaded();

	FVoiceAction Result;
	Result.OriginalUtterance = Utterance;

	if (Utterance.IsEmpty())
	{
		UE_LOG(LogTemp, Warning, TEXT("[NLP] Empty utterance received"));
		return Result;
	}

	// ─── Extract number if present ──────────────────────────────────
	Result.Quantity = ExtractNumber(Utterance);

	// ─── Match against known patterns ───────────────────────────────
	for (const FCommandPattern& Pattern : CommandPatterns)
	{
		FString LowerUtterance = Utterance.ToLower();
		
		for (const FString& Keyword : Pattern.Keywords)
		{
			if (LowerUtterance.Contains(Keyword.ToLower()))
			{
				Result.Type = Pattern.ActionType;
				
				// Extract target actor type or commodity name
				Result.Target = ExtractActorType(Utterance);
				if (Result.Target.IsEmpty())
				{
					Result.Target = ExtractCommodityName(Utterance);
				}

				UE_LOG(LogTemp, Log, TEXT("[NLP] Matched pattern: %d with target '%s'"), 
					static_cast<int32>(Pattern.ActionType), *Result.Target);
				break;
			}
		}

		if (Result.Type != EVoiceActionType::Unknown)
		{
			break;
		}
	}

	return Result;
}

int32 UNlpParser::ExtractNumber(const FString& Utterance) const
{
	int32 Number = 0;
	FString NumberStr;
	
	for (int32 i = 0; i < Utterance.Len(); ++i)
	{
		TCHAR C = Utterance[i];
		if (C >= '0' && C <= '9')
		{
			NumberStr += C;
		}
		else if (!NumberStr.IsEmpty())
		{
			break;
		}
	}

	if (!NumberStr.IsEmpty())
	{
		Number = FCString::Atoi(*NumberStr);
	}

	return Number;
}

FString UNlpParser::ExtractActorType(const FString& Utterance) const
{
	TArray<FString> ActorTypes = {
		TEXT("rock"), TEXT("tree"), TEXT("building"), TEXT("ship"),
		TEXT("station"), TEXT("asteroid"), TEXT("planet"), TEXT("moon")
	};

	FString LowerUtterance = Utterance.ToLower();
	for (const FString& Type : ActorTypes)
	{
		if (LowerUtterance.Contains(Type))
		{
			return Type;
		}
	}

	return TEXT("");
}

FString UNlpParser::ExtractCommodityName(const FString& Utterance) const
{
	TArray<FString> Commodities = {
		TEXT("titanium"), TEXT("iron"), TEXT("gold"), TEXT("silver"),
		TEXT("copper"), TEXT("aluminum"), TEXT("steel"), TEXT("uranium")
	};

	FString LowerUtterance = Utterance.ToLower();
	for (const FString& Commodity : Commodities)
	{
		if (LowerUtterance.Contains(Commodity))
		{
			return Commodity;
		}
	}

	return TEXT("");
}

FName UNlpParser::ResolvePropertyName(const FString& PropertyName) const
{
	// Map natural language property names to UE property paths
	FString LowerProp = PropertyName.ToLower();
	
	if (LowerProp.Contains(TEXT("brightness"))) return TEXT("Brightness");
	if (LowerProp.Contains(TEXT("color"))) return TEXT("Color");
	if (LowerProp.Contains(TEXT("material"))) return TEXT("Material");
	if (LowerProp.Contains(TEXT("visibility"))) return TEXT("Visibility");
	if (LowerProp.Contains(TEXT("scale"))) return TEXT("Scale");
	
	return *PropertyName;
}

bool UNlpParser::IsRecognizedCommand(const FString& Utterance)
{
	// Deprecated function - use ParseUtterance instead
	FVoiceAction Result = ParseUtterance(Utterance);
	return Result.Type != EVoiceActionType::Unknown;
}
