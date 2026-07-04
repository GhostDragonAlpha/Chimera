// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class Chimera : ModuleRules
{
	public Chimera(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		
		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"PCG",
			"AIModule",
			"GameplayAbilities",
			"Niagara",
			"NiagaraCore",
		});

		PrivateIncludePaths.AddRange(new string[] {
			"Chimera/ProceduralGenerated/Combat",
			"Chimera/ProceduralGenerated/AI",
			"Chimera/ProceduralGenerated/Flight",
			"Chimera/ProceduralGenerated/PCG",
			"Chimera/ProceduralGenerated/Stations",
			"Chimera/ProceduralGenerated/Missions",
			"Chimera/ProceduralGenerated/Factions",
			"Chimera/ProceduralGenerated/Save",
			"Chimera/ProceduralGenerated/GameMode",
			"Chimera/ProceduralGenerated/Ships",
			"Chimera/ProceduralGenerated/Tools",
		});
	}
}
