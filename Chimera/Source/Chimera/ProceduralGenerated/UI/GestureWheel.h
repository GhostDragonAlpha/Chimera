// Copyright 2026 Chimera Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "GestureWheel.generated.h"

class UImage;
class UTextBlock;
class UCanvasPanel;
class UOverlay;

/**
 * The seven social verbs. The only words in a wordless game.
 * Each maps to a slot on the radial wheel (clockwise from 12 o'clock).
 */
UENUM(BlueprintType)
enum class EChimeraGesture : uint8
{
    Wave     UMETA(DisplayName = "Wave"),
    Offer    UMETA(DisplayName = "Offer"),
    Refuse   UMETA(DisplayName = "Refuse"),
    Point    UMETA(DisplayName = "Point"),
    Kneel    UMETA(DisplayName = "Kneel"),
    Beckon   UMETA(DisplayName = "Beckon"),
    Thank    UMETA(DisplayName = "Thank"),
    None     UMETA(DisplayName = "None")
};

/**
 * Dispatched when the player commits a gesture (releases TAB with a
 * highlighted slot). Carries the actor who gestured and the intended
 * recipient (another actor, or nullptr for broadcast).
 */
USTRUCT(BlueprintType)
struct FGestureEvent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gesture")
    AActor* From = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gesture")
    AActor* To = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gesture")
    EChimeraGesture Gesture = EChimeraGesture::None;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnGestureCommitted, const FGestureEvent&, Event);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnWheelVisibilityChanged, bool, bIsOpen);