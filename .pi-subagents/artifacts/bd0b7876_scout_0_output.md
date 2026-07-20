---

# Code Context

## Files Retrieved

1. **`Chimera/Source/Chimera/ProceduralGenerated/Economy/CommodityData.h`** (full) — core commodity definition
2. **`Chimera/Source/Chimera/ProceduralGenerated/Economy/CommodityData.cpp`** (full) — constructor defaults and price formula
3. **`Chimera/Source/Chimera/ProceduralGenerated/Economy/EconomyInitializer.h`** (full) — BlueprintFunctionLibrary entry point
4. **`Chimera/Source/Chimera/ProceduralGenerated/Economy/EconomyInitializer.cpp`** (full) — DSL-generated seed data
5. **`Chimera/Source/Chimera/ProceduralGenerated/Economy/EconomyManager.h`** (full) — runtime manager component
6. **`Chimera/Source/Chimera/ProceduralGenerated/Economy/EconomyManager.cpp`** (full) — price tick, lookup, supply/demand adjustment
7. **`Chimera/Source/Chimera/ProceduralGenerated/Economy/StationTradingData.h`** (full) — per-station data (supporting)

---

## Key Code

### `UCommodityData` — exact field layout

```cpp
UCLASS(Blueprintable, BlueprintType)
class CHIMERA_API UCommodityData : public UDataAsset
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity")
    FString CommodityName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity")
    FString Description;                      // <--- declared but NEVER populated

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|Pricing")
    float BasePrice;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|SupplyDemand")
    float CurrentSupply;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|SupplyDemand")
    float CurrentDemand;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|SupplyDemand")
    float SupplyMultiplier;   // elasticity weight 0.0–1.0

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|SupplyDemand")
    float DemandMultiplier;   // elasticity weight 0.0–1.0

    UFUNCTION(BlueprintCallable, Category = "Commodity|Pricing")
    float CalculateCurrentPrice() const;
};
```

### `UCommodityData::CalculateCurrentPrice()` — pricing formula

```cpp
float ratio = (CurrentDemand + epsilon) / (CurrentSupply + epsilon);   // epsilon = 1.0
float elasticity = Clamp(SupplyMultiplier + DemandMultiplier, 0.1, 2.0);
float priceMultiplier = Pow(ratio, elasticity);
priceMultiplier = Clamp(priceMultiplier, 0.25, 4.0);
return BasePrice * priceMultiplier;
```

### Constructor defaults

```cpp
BasePrice = 100.0f;
CurrentSupply = 1000.0f;
CurrentDemand = 1000.0f;
SupplyMultiplier = 0.5f;
DemandMultiplier = 0.5f;
// Description is NOT defaulted → empty FString
```

### What the DSL generator actually populates (from `BuildEconomy`)

| Commodity       | BasePrice | Description set? |
|-----------------|-----------|------------------|
| Titanium        | 62.5      | **NO**           |
| Iron_Ore        | 30.0      | **NO**           |
| Synthetic_Food  | 15.0      | **NO**           |
| Quantum_Cores   | 5000.0    | **NO**           |

---

## Architecture

1. **`UCommodityData`** — `UDataAsset` subclass; each instance is one commodity with identity, pricing, supply/demand state, and a `CalculateCurrentPrice()` method.
2. **`UEconomyManager`** — `UActorComponent` that owns `TArray<UCommodityData*> CommodityList` and ticks `UpdateCommodityPrices()` each frame (applies small random supply/demand fluctuations, broadcasts `OnCommodityPriceChanged` when price moves > 0.1).
3. **`UEconomyInitializer`** — `UBlueprintFunctionLibrary` with a static `BuildEconomy()` that hard-codes 4 commodities and 3 stations.
4. **`UStationTradingData`** — per-station data with `TMap<FName, float> BuyPrices` / `SellPrices` for DSL-specified absolute prices, plus `BuyPriceMultiplier` / `SellPriceMultiplier` as fallback.
5. **Data flow**: `BeginPlay` → call `UEconomyInitializer::BuildEconomy(this)` → populates `CommodityList` & `StationTradingList` → `CalculateStationTradePrices` clamps multipliers → `Tick` calls `UpdateCommodityPrices` per frame.

---

## Start Here

Open **`CommodityData.h`** (the full header). It is the root data type that everything else depends on — every field name, category, and blueprint visibility is defined there.

---

## Key Findings & Risks

### Finding 1 — `Description` is a dead field (severity: **medium**)
- **File**: `CommodityData.h` line 16 — `FString Description` declared as `UPROPERTY`.
- **Evidence**: `CommodityData.cpp` constructor does not set it. `EconomyInitializer.cpp` never writes it for any of the 4 commodities. Runtime value = empty `FString`.
- **Risk**: If any UI, tooltip, or trading widget reads `Description`, it will show blank text. If a validation gate checks for non-empty descriptions, it will flag every commodity as incomplete.
- **Fix**: Either (a) have the DSL `GameCodeGenerator` emit a description string per commodity, or (b) add a default in the constructor (e.g., `Description = TEXT("A basic commodity.");`).

### Finding 2 — No supply/demand initial values in `BuildEconomy` (severity: **low**)
- The constructor defaults (`CurrentSupply = 1000.0f`, `CurrentDemand = 1000.0f`) mean all 4 commodities start at equilibrium (ratio = 1.0, price = BasePrice). This is fine for a prototype but means no differentiation unless mutated at runtime.

### Finding 3 — `SupplyMultiplier` / `DemandMultiplier` not customized per commodity (severity: **low**)
- All commodities use the constructor default `0.5f / 0.5f`. The `EconomyInitializer` never overrides them. Elasticity is uniform.

### Finding 4 — `StationTradingData` `BuyPriceMultiplier` / `SellPriceMultiplier` never set by initializer (severity: **medium**)
- The DSL initializer uses absolute `BuyPrices`/`SellPrices` `TMap` entries and never writes the multiplier fields. `CalculateStationTradePrices` in `BeginPlay` clamps them to `[0.1, 10.0]`, but since they were never set their default is `0.0f` (POD float), which gets clamped to `0.1f`. Stations that rely on the multiplier fallback will get a non-sensical 90% discount instead of the intended default behavior. However, the absolute `TMap` entries take priority in `GetBuyPriceForCommodity`/`GetSellPriceForCommodity`, so this only affects commodities NOT in the absolute price map.

---