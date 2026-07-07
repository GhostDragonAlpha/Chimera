import re

with open('core/game_code_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace FWeaponSlotData struct
old_weapon_slot = r'''USTRUCT\(BlueprintType\)
struct FWeaponSlotData \{
\tGENERATED_BODY\(\)

\tUPROPERTY\(EditAnywhere, Category = "Weapon"\)
\tFName Name;

\tUPROPERTY\(EditAnywhere, Category = "Weapon", meta = \(DisplayName = "Size"\)\)
\tFString Size; // S1, S2, S3

\tUPROPERTY\(EditAnywhere, Category = "Weapon", meta = \(ClampMin = "1"\)\)
\tint32 Count;

\tUPROPERTY\(EditAnywhere, Category = "Weapon", meta = \(DisplayName = "Type"\)\)
\tFString Type; // fixed, gimbal, remote_turret

\tUPROPERTY\(EditAnywhere, Category = "Combat Stats"\)
\tfloat FireRate;

\tUPROPERTY\(EditAnywhere, Category = "Combat Stats"\)
\tfloat DamagePerShot;

\tUPROPERTY\(EditAnywhere, Category = "Combat Stats"\)
\tfloat ProjectileSpeed;

\tUPROPERTY\(EditAnywhere, Category = "Combat Stats"\)
\tfloat Range;
\};'''

new_weapon_slot = '''USTRUCT(BlueprintType)
struct FWeaponSlotData {
\tGENERATED_BODY()

\tUPROPERTY(EditAnywhere, Category = "Weapon")
\tFName Name = NAME_None;

\tUPROPERTY(EditAnywhere, Category = "Weapon", meta = (DisplayName = "Size"))
\tFString Size = TEXT(""); // S1, S2, S3

\tUPROPERTY(EditAnywhere, Category = "Weapon", meta = (ClampMin = "0"))
\tint32 Count = 0;

\tUPROPERTY(EditAnywhere, Category = "Weapon", meta = (DisplayName = "Type"))
\tFString Type = TEXT("fixed"); // fixed, gimbal, remote_turret

\tUPROPERTY(EditAnywhere, Category = "Combat Stats")
\tfloat FireRate = 0.0f;

\tUPROPERTY(EditAnywhere, Category = "Combat Stats")
\tfloat DamagePerShot = 0.0f;

\tUPROPERTY(EditAnywhere, Category = "Combat Stats")
\tfloat ProjectileSpeed = 0.0f;

\tUPROPERTY(EditAnywhere, Category = "Combat Stats")
\tfloat Range = 0.0f;
};'''

content = re.sub(old_weapon_slot, new_weapon_slot, content)

# Replace FMissileRackData struct
old_missile_rack = r'''USTRUCT\(BlueprintType\)
struct FMissileRackData \{
\tGENERATED_BODY\(\)

\tUPROPERTY\(EditAnywhere, Category = "Missiles"\)
\tFName RackName;

\tUPROPERTY\(EditAnywhere, Category = "Missiles", meta = \(ClampMin = "1"\)\)
\tint32 Count;

\tUPROPERTY\(EditAnywhere, Category = "Missiles"\)
\tFString MissileType;

\tUPROPERTY\(EditAnywhere, Category = "Combat Stats"\)
\tfloat Damage;

\tUPROPERTY\(EditAnywhere, Category = "Combat Stats"\)
\tfloat TrackingStrength;
\};'''

new_missile_rack = '''USTRUCT(BlueprintType)
struct FMissileRackData {
\tGENERATED_BODY()

\tUPROPERTY(EditAnywhere, Category = "Missiles")
\tFName RackName = NAME_None;

\tUPROPERTY(EditAnywhere, Category = "Missiles", meta = (ClampMin = "0"))
\tint32 Count = 0;

\tUPROPERTY(EditAnywhere, Category = "Missiles")
\tFString MissileType = TEXT("");

\tUPROPERTY(EditAnywhere, Category = "Combat Stats")
\tfloat Damage = 0.0f;

\tUPROPERTY(EditAnywhere, Category = "Combat Stats")
\tfloat TrackingStrength = 0.0f;
};'''

content = re.sub(old_missile_rack, new_missile_rack, content)

with open('core/game_code_generator.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Successfully replaced struct definitions')
