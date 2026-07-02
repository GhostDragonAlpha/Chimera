# UE5 API Extraction Verification Report
Generated from: `E:\PythonChimera\Chimera\docs\ue5_api_extracted.json`

## Summary

- **Top-level paths**: 423
- **Distinct module names**: 1056
- **Total type entries (sum across modules)**: 24886
- **Unique type names (deduplicated)**: 24150
- **UCLASS**: 9982
- **USTRUCT**: 10263
- **UENUM**: 3905

---

## Step 1: PCG Types Comparison

### Classes from Manual Encoding Found in Extraction
- **UPCGData** (class): found with 2 properties
  - Matched properties: UID, Metadata
  - **MISSING properties**: Crc
  - Specifiers: [['MinimalAPI', None], ['BlueprintType', None], ['ClassGroup', '(Procedural)']]
- **FPCGTaggedData** (struct): found with 5 properties
  - Matched properties: Data, Tags, Pin, bPinlessData, bIsUsedMultipleTimes
  - Specifiers: [['BlueprintType', None]]
- **FPCGDataCollection** (struct): found with 2 properties
  - Matched properties: TaggedData, bCancelExecutionOnEmpty
  - **MISSING properties**: bCancelExecution, DataCrcs
  - Specifiers: [['BlueprintType', None]]

### Enums from Manual Encoding Found in Extraction
- **EPCGDataUsage** (enum): found
  - Matched values: None, GraphExecutorTaskOutput, ComponentOutputData, ComponentPerPinOutputData, ComponentInspectionData

### Additional PCG Types Found in Extraction (Not in Manual Encoding)
- `APCGBuilderVolume`
- `APCGPartitionActor`
- `APCGVolume`
- `APCGWorldActor`
- `AProceduralFoliageBlockingVolume`
- `AProceduralFoliageVolume`
- `AProceduralMeshActor`
- `ECEClonerEffectorProceduralPattern`
- `EChaosClothAssetProceduralSelectionType`
- `EPCGActorFilter`
- `EPCGActorSelection`
- `EPCGAlignPointsAxisReferential`
- `EPCGAlignPointsSpatialReferential`
- `EPCGAppendMeshesFromPointsMode`
- `EPCGApplyHierarchyOption`
- `EPCGAssetListSource`
- `EPCGAttachOptions`
- `EPCGAttractMode`
- `EPCGAttributeAccessorFlags`
- `EPCGAttributeFilterOperation`
- `EPCGAttributeFilterOperator`
- `EPCGAttributeInheritanceMode`
- `EPCGAttributeNoiseMode`
- `EPCGAttributePropertySelection`
- `EPCGAttributeReduceOperation`
- `EPCGAttributeRemapMode`
- `EPCGAttributeSelectAxis`
- `EPCGAttributeSelectOperation`
- `EPCGBlurElementMode`
- `EPCGBooleanOperationMode`
- `EPCGBooleanOperationTagInheritanceMode`
- `EPCGBoundsModifierMode`
- `EPCGChangeType`
- `EPCGClipPathOperation`
- `EPCGClusterAlgorithm`
- `EPCGCollapseComparisonMode`
- `EPCGCollapseMode`
- `EPCGCollapseVisitOrder`
- `EPCGCollisionQueryFlag`
- `EPCGCollisionShapeType`
- `EPCGColorChannel`
- `EPCGComponentDirtyFlag`
- `EPCGComponentGenerationTrigger`
- `EPCGComponentInput`
- `EPCGComponentSelection`
- `EPCGComputeKernelFlags`
- `EPCGContainerType`
- `EPCGControlFlowSelectionMode`
- `EPCGControlPointFuseMode`
- `EPCGCoordinateSpace`
- `EPCGCopyAttributesOperation`
- `EPCGCopyPointsInheritanceMode`
- `EPCGCopyPointsMetadataInheritanceMode`
- `EPCGCopyPointsTagInheritanceMode`
- `EPCGCreatePolygonDefaultNormalBehavior`
- `EPCGCreatePolygonInputType`
- `EPCGCreateSplineMode`
- `EPCGCullPointsMode`
- `EPCGDataCountMode`
- `EPCGDataLayerSource`
- `EPCGDataMultiplicity`
- `EPCGDataOverrideKeyPolicy`
- `EPCGDataOverridePhase`
- `EPCGDataType`
- `EPCGDataViewAttributeLayout`
- `EPCGDataViewCSVOutput`
- `EPCGDebugVisScaleMethod`
- `EPCGDensityMergeOperation`
- `EPCGDifferenceDensityFunction`
- `EPCGDifferenceMode`
- `EPCGEditorDirtyMode`
- `EPCGEditorDoubleClickAction`
- `EPCGEditorNewPCGGraphBehavior`
- `EPCGEditorNewSettingsBehavior`
- `EPCGElementCountMode`
- `EPCGElementDimension`
- `EPCGElementMultiplicity`
- `EPCGElementType`
- `EPCGExclusiveDataType`
- `EPCGExecutionPhase`
- ... and 713 more

---

## Step 2: Niagara Types Presence

| Type | Present | Type Kind | Properties | Functions | Values/Specifiers |
|------|---------|-----------|------------|-----------|-------------------|
| `UNiagaraSystem` | Yes | class | 47 | 0 | specifiers: [['BlueprintType', None], ['MinimalAPI', None]] |
| `UNiagaraComponent` | Yes | class | 22 | 79 | specifiers: [['ClassGroup', '(Rendering, Common)'], ['Blueprintable', None], ['hidecategories', 'Object'], ['hidecategories', 'Physics'], ['hidecategories', 'Collision'], ['showcategories', 'Trigger'], ['editinlinenew', None], ['MinimalAPI', None]] |
| `UNiagaraEmitter` | Yes | class | 44 | 0 | specifiers: [['MinimalAPI', None]] |
| `FNiagaraFloat` | Yes | struct | 1 | 0 |  |
| `FNiagaraBool` | Yes | struct | 0 | 0 |  |
| `FNiagaraMatrix` | Yes | struct | 4 | 0 |  |
| `ENiagaraExecutionState` | Yes | enum | 0 | 0 | values: Active, Inactive, InactiveClear, Complete, Disabled UMETA, Num UMETA |

---

## Step 3: Module Coverage

| Module | Found as Module | Type Count | Sample Types | Matching Paths |
|--------|----------------|------------|--------------|----------------|
| Engine | Yes | 2992 | `UDataflowAttachment`, `UDataflowBlueprintLibrary`, `FDataflowVariable`, `UDataflowBaseContent`, `UDataflowSkeletalContent` |  |
| Niagara | Yes | 506 | `UNiagaraBakerOutput`, `FNiagaraBakerTextureSource`, `UNiagaraBakerOutputSimCache`, `UNiagaraBakerOutputSparseVolumeTexture`, `UNiagaraBakerOutputStaticMesh` | Plugins/Niagara |
| PCG | Yes | 695 | `UPCGAssetExporter`, `FPCGAssetExporterParameters`, `UPCGAssetExporterUtils`, `FPCGRuntimeGenerationRadii`, `EPCGChangeType` | Plugins/PCG |
| Chaos | Yes | 52 | `FChaosSolverDestructionSettings`, `FChaosSolverConfiguration`, `EClusterUnionMethod`, `EChaosSolverTickMode`, `EChaosThreadingMode` |  |
| Renderer | **NO** | 0 |  |  |

**Renderer** not found as a module name but related types exist across other modules:
- `UFoliageType_ActorThumbnailRenderer` (in module `FoliageEdit`)
- `UFoliageType_ISMThumbnailRenderer` (in module `FoliageEdit`)
- `UWidgetBlueprintThumbnailRenderer` (in module `UMGEditor`)
- `UTexture2DArrayThumbnailRenderer` (in module `UnrealEd`)
- `UTextureCubeArrayThumbnailRenderer` (in module `UnrealEd`)
- `UTextureCubeThumbnailRenderer` (in module `UnrealEd`)
- `UAnimBlueprintThumbnailRenderer` (in module `UnrealEd`)
- `UAnimSequenceThumbnailRenderer` (in module `UnrealEd`)
- `UBlendSpaceThumbnailRenderer` (in module `UnrealEd`)
- `UBlueprintThumbnailRenderer` (in module `UnrealEd`)
- `UClassThumbnailRenderer` (in module `UnrealEd`)
- `UCurveFloatThumbnailRenderer` (in module `UnrealEd`)
- `UCurveVector3ThumbnailRenderer` (in module `UnrealEd`)
- `UCurveLinearColorThumbnailRenderer` (in module `UnrealEd`)
- `UDefaultSizedThumbnailRenderer` (in module `UnrealEd`)
- `UFontThumbnailRenderer` (in module `UnrealEd`)
- `ULevelThumbnailRenderer` (in module `UnrealEd`)
- `UMaterialFunctionThumbnailRenderer` (in module `UnrealEd`)
- `UMaterialInstanceThumbnailRenderer` (in module `UnrealEd`)
- `UNeuralProfileRenderer` (in module `UnrealEd`)
- ... and 30 more
| RenderCore | Yes | 2 | `EVTProducerPriority`, `EVTInvalidatePriority` |  |
| UMG | Yes | 188 | `UMovieScene2DTransformPropertySystem`, `UMovieScene2DTransformSection`, `FMovieScene2DTransformMask`, `UMovieScene2DTransformTrack`, `UMovieSceneMarginSection` |  |
| GameplayAbilities | Yes | 258 | `UAbilitySystemBlueprintLibrary`, `FGameplayTagChangedEventWrapperSpecHandle`, `UAbilitySystemComponent`, `EGameplayEffectReplicationMode`, `UAbilitySystemDebugHUDExtension` | Plugins/GameplayAbilities |
| EnhancedInput | Yes | 74 | `FEnhancedActionKeyMapping`, `EPlayerMappableKeySettingBehaviors`, `UEnhancedInputActionDelegateBinding`, `UEnhancedInputActionValueBinding`, `FBlueprintEnhancedInputActionBinding` | Plugins/EnhancedInput |
| Metasound | **NO** | 0 |  | Plugins/Metasound |

**Metasound** not found as a module name but related types exist across other modules:
- `UMetasoundOfflinePlayerComponent` (in module `HarmonixMetasound`)
- `FMetasoundMusicClockSettings` (in module `HarmonixMetasound`)
- `UHarmonixMetasoundMusicAsset` (in module `HarmonixMetasound`)
- `UMetasoundMusicSource` (in module `HarmonixMetasound`)
- `FMetasoundMusicSourceSettings` (in module `HarmonixMetasound`)
- `UMetaSoundEditorBuilderListener` (in module `MetasoundEditor`)
- `UMetasoundEditorGraphMemberDefaultLiteral` (in module `MetasoundEditor`)
- `UMetasoundEditorGraphMember` (in module `MetasoundEditor`)
- `UMetasoundEditorGraphVertex` (in module `MetasoundEditor`)
- `UMetasoundEditorGraphInput` (in module `MetasoundEditor`)
- `UMetasoundEditorGraphOutput` (in module `MetasoundEditor`)
- `UMetasoundEditorGraphVariable` (in module `MetasoundEditor`)
- `UMetasoundEditorGraph` (in module `MetasoundEditor`)
- `FMetasoundEditorGraphMemberBreadcrumb` (in module `MetasoundEditor`)
- `FMetasoundEditorGraphVertexBreadcrumb` (in module `MetasoundEditor`)
- `FMetasoundEditorGraphVariableBreadcrumb` (in module `MetasoundEditor`)
- `UMetasoundEditorGraphCommentNode` (in module `MetasoundEditor`)
- `UMetasoundEditorGraphInputNode` (in module `MetasoundEditor`)
- `UMetasoundEditorGraphMemberDefaultBool` (in module `MetasoundEditor`)
- `UMetasoundEditorGraphMemberDefaultBoolArray` (in module `MetasoundEditor`)
- ... and 30 more
| CommonUI | Yes | 78 | `UAnalogSlider`, `FCommonInputActionHandlerData`, `UCommonActionWidget`, `UCommonActivatableWidget`, `UCommonActivatableWidgetSwitcher` | Plugins/CommonUI |

---

## Step 4: Type Breakdown

- **Total unique type entries**: 24150
- **UCLASS**: 9982
- **USTRUCT**: 10263
- **UENUM**: 3905
- **Total UFUNCTIONs** (across all classes): 20438
- **Total UPROPERTYs** (across all classes): 63289
- **Delegates**: 0
- **Typedefs**: 0
- **Interfaces**: 0
- **Other/Unclassified**: 0

### Category Breakdown

| Category | Count |
|----------|-------|
| USTRUCT | 10263 |
| UCLASS | 9982 |
| UENUM | 3905 |

### Examples by Type

- UCLASS examples: UAnimationCompressionLibraryDatabase, UAnimBoneCompressionCodec_ACL, UAnimBoneCompressionCodec_ACLBase, UAnimBoneCompressionCodec_ACLCustom, UAnimBoneCompressionCodec_ACLDatabase
- USTRUCT examples: FAISchemaAction_AddComment, FAISchemaAction_NewNode, FAISchemaAction_NewSubNode, FGraphNodeClassData, FFeaturePackLevelSet
- UENUM examples: ACLVisualFidelity, ACLVisualFidelityChangeResult, ACLRotationFormat, ACLVectorFormat, ACLCompressionLevel
- Delegate examples: 

---

## Top 30 Modules by Type Count

| Module | Type Count | Paths |
|--------|-----------|-------|
| Engine | 2992 | Source/Runtime |
| UnrealEd | 697 | Source/Editor |
| ControlRig | 695 | Plugins/ControlRig |
| PCG | 695 | Plugins/PCG |
| RigVM | 575 | Plugins/RigVM |
| Niagara | 506 | Plugins/Niagara |
| GeometryCollectionNodes | 428 | Plugins/GeometryCollectionPlugin |
| MeshModelingTools | 299 | Plugins/MeshModelingToolset |
| CoreUObject | 283 | Source/Runtime |
| GeometryScriptingCore | 275 | Plugins/GeometryScripting |
| AIModule | 262 | Source/Runtime |
| NiagaraEditor | 262 | Plugins/Niagara |
| GameplayAbilities | 258 | Plugins/GameplayAbilities |
| GameplayCameras | 256 | Plugins/GameplayCameras |
| Runtime | 253 | Plugins/AnimationLocomotionLibrary |
| MovieScene | 239 | Source/Runtime |
| MovieSceneTracks | 233 | Source/Runtime |
| MovieRenderPipelineCore | 213 | Plugins/MovieRenderPipeline |
| MeshModelingToolsExp | 211 | Plugins/MeshModelingToolsetExp |
| IKRig | 191 | Plugins/IKRig |
| Mover | 189 | Plugins/Mover |
| UMG | 188 | Source/Runtime |
| InteractiveToolsFramework | 183 | Source/Runtime |
| ConcertSyncCore | 171 | Plugins/Concert |
| TextureGraph | 171 | Plugins/TextureGraph |
| BlueprintGraph | 163 | Source/Editor |
| AnimGraphRuntime | 158 | Source/Runtime |
| StateTreeModule | 152 | Plugins/StateTree |
| AnimDatabase | 141 | Plugins/Animation |
| AnimGraph | 127 | Source/Editor |

---

## Assessment: Is the extraction complete enough to auto-populate the DSL?

### Gap Analysis

- **PCG Classes**: 3/3 found (0 missing)
- **PCG Enums**: 1/1 found (0 missing)
- **Extra PCG types found by extractor**: 793
- **Niagara types**: 7/7 found
- **Modules present**: 9/11

**Verdict: Extraction is COMPLETE for all critical types.**
All manually encoded PCG classes/enums and all key Niagara types are present.
The extraction is suitable to auto-populate the DSL with minimal manual supplementation.

The extraction overall contains **24,150** types (9,982 UCLASS, 10,263 USTRUCT, 3,905 UENUM), which is a substantial corpus.
It spans **1056** modules across **423** paths, covering much of the UE5 API surface.