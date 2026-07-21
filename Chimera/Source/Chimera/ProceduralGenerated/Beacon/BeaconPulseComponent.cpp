// BeaconPulseComponent — makes the beacon pulse at trained rates.
// The Mirror of Erised: costless life = dim signal, generous life = bright signal.
#include "BeaconPulseComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "SacrificeLogComponent.h"

UBeaconPulseComponent::UBeaconPulseComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickGroup = TG_PrePhysics;
    PulseRate0Helps = 0.18f;
    PulseRate3Helps = 1.55f;
    CurrentColor0 = FLinearColor(1.0f, 0.08f, 0.03f);
    CurrentColor3 = FLinearColor(1.0f, 0.85f, 0.45f);
    BaseIntensity = 50000.0f;
    HelpCount = 0;
    ElapsedTime = 0.0f;
}

void UBeaconPulseComponent::BeginPlay()
{
    Super::BeginPlay();
    LightComp = GetOwner()->FindComponentByClass<UPointLightComponent>();
}

void UBeaconPulseComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!LightComp) return;
    
    // Query the player's sacrifice log for actual help count
    if (GetWorld())
    {
        APlayerController* PC = GetWorld()->GetFirstPlayerController();
        if (PC && PC->GetPawn())
        {
            USacrificeLogComponent* SacLog = PC->GetPawn()->FindComponentByClass<USacrificeLogComponent>();
            if (SacLog)
            {
                int32 NewCount = SacLog->GetSacrificeCount();
                if (NewCount != HelpCount)
                {
                    HelpCount = NewCount;
                    UE_LOG(LogTemp, Display, TEXT("[MIRROR] Beacon help count = %d — pulse rate = %.2f Hz"),
                        HelpCount, FMath::Lerp(PulseRate0Helps, PulseRate3Helps, FMath::Min((float)HelpCount / 3.0f, 1.0f)));
                }
            }
        }
    }
    
    ElapsedTime += DeltaTime;
    float T = FMath::Min((float)HelpCount / 3.0f, 1.0f);
    float PulseRate = FMath::Lerp(PulseRate0Helps, PulseRate3Helps, T);
    float Pulse = FMath::Sin(ElapsedTime * PulseRate * 2.0f * PI) * 0.5f + 0.5f;
    LightComp->SetIntensity(BaseIntensity * (0.2f + Pulse * 0.8f));
    FLinearColor Color = FLinearColor::LerpUsingHSV(CurrentColor0, CurrentColor3, T);
    LightComp->SetLightColor(Color);
}

void UBeaconPulseComponent::SetHelpCount(int32 Count)
{
    HelpCount = FMath::Max(0, Count);
}
