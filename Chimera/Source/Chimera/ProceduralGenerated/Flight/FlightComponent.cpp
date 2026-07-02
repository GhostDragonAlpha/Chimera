#include "FlightComponent.h"
UFlightComponent::UFlightComponent(const FObjectInitializer& ObjectInitializer) : Super(ObjectInitializer) { PrimaryComponentTick.bCanEverTick = true; }
void UFlightComponent::InitializeFromShip(float, float, float, float) {}
