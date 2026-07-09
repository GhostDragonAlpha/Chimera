// Copyright Epic Games, Inc. All Rights Reserved.

using System.IO;
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
			"Chimera/ProceduralGenerated/Sound",
			"Chimera/ProceduralGenerated/Interactions",
			"ThirdParty/whisper.cpp/whisper-src/include"
		});

		// Add whisper.cpp library paths and definitions
		PublicIncludePaths.AddRange(new string[] {
			"ThirdParty/whisper.cpp"
		});
		PublicIncludePaths.AddRange(new string[] {
			"ThirdParty/whisper.cpp/whisper-src/include"
		});
		PrivateIncludePaths.AddRange(new string[] {
			"ThirdParty/whisper.cpp/whisper-src/include"
		});

		// Note: WhisperWrapper.cpp is compiled separately via its own module or build system

		// Add precompiled whisper library if available
		string WhisperLibDir = Path.Combine(ModuleDirectory, "../ThirdParty/whisper.cpp/whisper-src/build/lib/Release");
		if (Directory.Exists(WhisperLibDir)) {
			PublicAdditionalLibraries.Add(Path.Combine(WhisperLibDir, "whisper.lib"));
		}
	}
}
