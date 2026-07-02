# UE 5.8 Subsystem API Inventory

## 1. Plugins List (UE_5.8/Engine/Plugins/)

The following plugins are available in UE 5.8, each representing a potential DSL block:

**2D**, **AI**, **Animation**, **AudioGameplay**, **AudioGameplayVolume**, **AudioInsights**, **AutomationControllerRpc**, **BaseMaterial**, **BlueprintFileUtils**, **Bridge**, **Cameras**, **ChaosCloth**, **ChaosVD**, **Chooser**, **CmdLinkServer**, **Compositing**, **Compression**, **Dataflow**, **DerivedDataBuildController**, **Developer**, **DiscoveryBeaconReceiver**, **Editor**, **EnginePlugin_A**, **EnhancedInput**, **Enterprise**, **Experimental**, **Fab**, **FastBuildController**, **FX**, **GameInputWindows**, **Importers**, **Interchange**, **IoStoreInsights**, **JsonBlueprintUtilities**, **LightWeightInstancesEditor**, **MassInsights**, **Media**, **MegascansPlugin**, **MemoryUsageQueries**, **MeshPainting**, **Messaging**, **MetaHuman**, **MovieScene**, **Mutable**, **NetcodeUnitTest**, **NNE**, **Online**, **PCG**, **PCGInterops**, **Performance**, **Portal**, **Protocols**, **RenderGraphInsights**, **RenderTraceInsights**, **RPCBase**, **Runtime**, **ScriptGeneratorPlugin**, **ScriptPlugin**, **Slate**, **SubtitlesAndClosedCaptions**, **Tests**, **TextureGraph**, **TraceUtilities**, **UbaController**, **VirtualProduction**, **Web**, **WorldMetrics**, **XGEController

---

## 2. PCG (Procedural Content Generation) Subsystem

### Key Classes and Public Properties

**UPCGData** (Base data class)
- `UID` (uint64): Unique ID for object instance
- `Crc` (FPCGCrc): CRC for this object instance
- `Metadata` (UPCGMetadata*): Metadata pointer

**FPCGTaggedData**
- `Data` (FPCGDataPtrWrapper): Wraps TObjectPtr<const UPCGData>
- `Tags` (TSet<FString>): Data tags
- `Pin` (FName): Label of the pin data was emitted from/received on
- `bPinlessData` (bool): Special flag for data forwarded without a pin
- `bIsUsedMultipleTimes` (bool): Flag for multi-use optimization

**FPCGDataCollection**
- `TaggedData` (TArray<FPCGTaggedData>): Collection of tagged data items
- `bCancelExecutionOnEmpty` (bool): Cancel execution on empty (deprecated)
- `bCancelExecution` (bool): Cancel further computation flag
- `DataCrcs` (TArray<FPCGCrc>): Per-data CRC capturing tags, data, output pin

**EPCGDataUsage** (Flags enum)
- `None`, `GraphExecutorTaskOutput`, `ComponentOutputData`, `ComponentPerPinOutputData`, `ComponentInspectionData

---

## 3. Niagara Subsystem

### Key Classes and Public Properties

**Parameter Type Structs:**
- `FNiagaraFloat`: `Value` (float)
- `FNiagaraInt32`: `Value` (int32)
- `FNiagaraBool`: `Value` (int32, True=INDEX_NONE/-1, False=0)
- `FNiagaraPosition`: Inherits from FVector3f (X, Y, Z coordinates)
- `FNiagaraHalf`, `FNiagaraHalfVector2`, `FNiagaraHalfVector3`, `FNiagaraHalfVector4`: 16-bit half float types with x, y, z, w components

**Complex Types:**
- `FNiagaraMatrix`: Row0, Row1, Row2, Row3 (each FVector4f)
- `FNiagaraEmitterID`: `ID` (int32)
- `FNiagaraSpawnInfo`: `Count`, `InterpStartDt`, `IntervalDt`, `SpawnGroup`
- `FNiagaraID`: `Index`, `AcquireTag`
- `FNiagaraRandInfo`: `Seed1`, `Seed2`, `Seed3` (int32)

**Core Enums:**
- `ENiagaraStructConversionType`: CopyOnly, DoubleToFloat, Vector2, Vector3, Vector4, Quat
- `ENiagaraExecutionState`: Active, Inactive, InactiveClear, Complete, Disabled
- `ENiagaraExecutionStateManagement`: Awaken, SleepAndLetParticlesFinish, SleepAndClearParticles, KillImmediately, KillAfterParticlesFinish
- `ENiagaraCoordinateSpace`: Simulation, World, Local
- `ENiagaraOrientationAxis`: XAxis, YAxis, ZAxis

**Type Definition:**
- `FNiagaraTypeDefinition`: Core type system with ClassStructOrEnum, UnderlyingType, Flags, Size, Alignment

---

## 4. Chaos Physics Subsystem

### Key Classes and Public Properties

**EClusterUnionMethod** (enum)
- PointImplicit, DelaunayTriangulation, MinimalSpanningSubsetDelaunayTriangulation, PointImplicitAugmentedWithMinimalDelaunay, BoundsOverlapFilteredDelaunayTriangulation, None

**FChaosSolverDestructionSettings**
- `PerAdvanceBreaksAllowed` (int32): Number of breaks allowed per Advance invocation
- `PerAdvanceBreaksRescheduleLimit` (int32): Breaks rescheduled for next frame limit
- `ClusteringParticleReleaseThrottlingMinCount` (int32): Min active geometry collections before throttling
- `ClusteringParticleReleaseThrottlingMaxCount` (int32): Max active geometry collections for instant disable
- `bOptimizeForRuntimeMemory` (bool): Avoid creating physics data until root breaks

**FChaosSolverConfiguration**
- `PositionIterations` (int32): Number of position iterations during constraint solver step
- `VelocityIterations` (int32): Number of velocity iterations during constraint solver step
- `ProjectionIterations` (int32): Number of projection iterations during constraint solver step
- `CollisionMarginFraction` (float): Collision margin as fraction of size for boxes/convex shapes
- `CollisionMarginMax` (float): Upper limit on collision margin
- `CollisionCullDistance` (float): Max distance before not calculating nearest features
- `CollisionMaxPushOutVelocity` (float): Max speed for extracting inter-penetrating bodies
- `CollisionInitialOverlapDepenetrationVelocity` (float): Speed for initially-overlapping objects to depenetrate
- `ClusterConnectionFactor` (float): Cluster connection factor
- `ClusterUnionConnectionType` (EClusterUnionMethod): Cluster union method type
- `DestructionSettings` (FChaosSolverDestructionSettings): Destruction settings
- `bGenerateCollisionData` (bool): Generate collision data flag
- `CollisionFilterSettings` (FSolverCollisionFilterSettings): Collision filter settings
- `bGenerateBreakData` (bool): Generate break data flag
- `BreakingFilterSettings` (FSolverBreakingFilterSettings): Breaking filter settings
- `bGenerateTrailingData` (bool): Generate trailing data flag
- `TrailingFilterSettings` (FSolverTrailingFilterSettings): Trailing filter settings

---

## 5. Materials Subsystem

### Key Classes (Engine/Classes/)

**UMaterialInterface**: Base material interface class used across components and engine systems
**UMaterialBillboardComponent**: Billboard component with material support
**UMaterialInstanceDynamic**: Dynamic material instance for runtime modification
**UMaterialParameterCollection**: Material parameter collection for sharing parameters
**UMaterialParameterCollectionInstance**: Instance of material parameter collection

Materials are accessed via:
- `UPrimitiveComponent::SetMaterial()`
- `UMaterialInterface` references in components (BrushComponent, DecalComponent, InstancedSkinnedMeshComponent, LightComponent, MeshComponent, ModelComponent, PrimitiveComponent, StaticMeshComponent, TextRenderComponent)
- Particle system materials via `ParticleModuleMaterialBase`, `ParticleModuleMeshMaterial`

---

## 6. MetaSounds Subsystem

### Key Classes and Components

**MetasoundFrontend Core:**
- `FMetasoundAssetKey`: Asset identification key
- `FMetasoundAssetManager`: Asset management subsystem
- `FMetasoundAssetManagerTransaction`: Asset transaction handling
- `FMetasoundArrayNodes`, `FMetasoundAutoConverterNode`: Array and conversion nodes

**MetasoundEditor:**
- `IMetasoundEditor`: Editor interface
- `FMetasoundEditorDocumentClipboardUtils`: Document clipboard utilities
- `FMetasoundEditorGraphBuilder`: Graph building utilities
- `SMetasoundGraphNode`, `SMetasoundGraphPin`: UI node and pin components

---

## 7. Lighting/Lumen (Renderer) Subsystem

### Key Classes and Public Properties

**FGlobalDistanceFieldParameterData:**
- `TranslatedCenterAndExtent[MaxClipmaps]` (FVector4f[]): Translated center and extent per clipmap
- `TranslatedWorldToUVAddAndMul[MaxClipmaps]` (FVector4f[]): World to UV transform add/mul
- `MipTranslatedWorldToUVScale[MaxClipmaps]` (FVector4f[]): Mip scale transforms
- `MipTranslatedWorldToUVBias[MaxClipmaps]` (FVector4f[]): Mip bias transforms
- `MipFactor`, `MipTransition` (float): Mip parameters
- `PageAtlasTexture`, `CoverageAtlasTexture`, `PageTableTexture`, `MipTexture` (FRHITexture*): Texture resources
- `PageObjectGridBuffer` (FRDGPooledBuffer*): Page object grid buffer
- `ClipmapSizeInPages`, `MaxPageNum`, `NumGlobalSDFClipmaps` (int32): Clipmap configuration
- `InvPageAtlasSize`, `InvCoverageAtlasSize` (FVector): Inverse atlas sizes
- `GlobalDFResolution`, `MaxDFAOConeDistance` (float): Global distance field resolution and AO cone distance

**FGlobalDistanceFieldParameters2:**
Shader parameters including:
- `GlobalDistanceFieldPageAtlasTexture`, `GlobalDistanceFieldCoverageAtlasTexture`, `GlobalDistanceFieldPageTableTexture`, `GlobalDistanceFieldMipTexture` (Texture3D)
- `GlobalVolumeTranslatedCenterAndExtent[]`, `GlobalVolumeTranslatedWorldToUVAddAndMul[]` arrays
- `GlobalDistanceFieldMipTranslatedWorldToUVScale[]`, `GlobalDistanceFieldMipTranslatedWorldToUVBias[]` arrays
- `GlobalDistanceFieldMipFactor`, `GlobalDistanceFieldMipTransition`, `GlobalDistanceFieldClipmapSizeInPages` (float/int32)
- `GlobalDistanceFieldInvPageAtlasSize`, `GlobalDistanceFieldInvCoverageAtlasSize` (FVector3f)
- `GlobalVolumeDimension`, `GlobalVolumeTexelSize`, `MaxGlobalDFAOConeDistance` (float)
- `NumGlobalSDFClipmaps` (uint32)
- `CoveredExpandSurfaceScale`, `NotCoveredExpandSurfaceScale`, `NotCoveredMinStepScale`, `DitheredTransparencyStepThreshold`, `DitheredTransparencyTraceThreshold` (float)
- Sampler states for coverage, page atlas, and mip textures

**Renderer Public Headers:**
- `ComputeSystemInterface.h`, `FXRenderingUtils.h`, `GlobalDistanceFieldConstants.h`, `GpuDebugRendering.h`, `GPUSceneWriter.h`, `HairStrandsInterface.h`, `HdrCustomResolveShaders.h`, `LightMapHelpers.h`, `MaterialShader.h`, `MeshDrawShaderBindings.h`, `MeshEdges.h`, `MeshMaterialShader.h`, `MeshPassProcessor.h`, `RayTracingDynamicGeometryUpdateManager.h`, `RayTracingGeometryInstance.h`, `RayTracingInstance.h`, `SceneRenderTargetParameters.h`, `SceneUniformBuffer.h`

---

## Summary: Subsystems with Clear API Surfaces for Encoding

| Subsystem | API Surface Quality | Key Parameters Exposed |
|-----------|---------------------|------------------------|
| **PCG** | High | Data collections, tagged data, metadata domains, attribute selectors, CRC caching |
| **Niagara** | Very High | Float/int32/bool types, vectors (2D/3D/4D), half-float variants, matrices, spawn info, IDs, execution states, coordinate spaces |
| **Chaos Physics** | High | Iteration counts (position/velocity/projection), collision margins/culling/push-out velocities, clustering factors, destruction settings |
| **Materials** | Medium-High | Material interfaces, material instances, parameter collections, dynamic materials |
| **MetaSounds** | Medium | Asset keys, array nodes, auto-converter nodes, frontend registry, graph controllers |
| **Lumen/Renderer** | High | Global distance field clipmaps (max 8), world-to-UV transforms, mip factors/transitions, atlas sizes, AO cone distances, shader texture parameters |

All six subsystems have well-defined API surfaces with clear parameter structures that can be encoded into DSL blocks. Niagara and PCG offer the most comprehensive parameter type systems, while Chaos provides detailed physics solver configuration parameters, and the Renderer/Lumen system exposes detailed global distance field rendering parameters for lighting calculations.
