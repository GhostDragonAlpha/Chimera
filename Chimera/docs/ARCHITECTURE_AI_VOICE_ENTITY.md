# Chimera AI Voice Entity — Architecture Design

## 1. Concept

An in-game AI entity (the "Voice") that the player can talk to via voice commands, like a Star Trek computer or JARVIS. The Voice can:

- **Spawn/modify/delete actors** ("spawn a rock here", "make the sky darker")
- **Manipulate game state** ("give me 100 credits", "save the game")
- **Navigate/move** ("take me to the sand basin")
- **Query the world** ("what's my current position?", "how many actors are in this level?")
- **Execute economy/trade/mission operations** (existing DemoTerminal commands, now voice-accessible)
- **Answer questions about the game state** via LLM integration

The Voice is both a gameplay feature and a development tool — GMs can use it to debug/test without leaving the game.

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     PLAYER SPEAKS                            │
└──────────────────┬──────────────────────────────────────────┘
                   │ (audio stream)
┌──────────────────▼──────────────────────────────────────────┐
│  AChimeraVoiceEntity (in-game AI actor)                      │
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────────┐ │
│  │ Voice       │───▶│ Speech-to-   │───▶│ Natural        │ │
│  │ Capture     │    │ Text (STT)   │    │ Language       │ │
│  │ Component   │    │              │    │ Parser         │ │
│  └─────────────┘    └──────────────┘    └────────┬───────┘ │
│                                                   │         │
│  ┌─────────────┐    ┌──────────────┐    ┌────────▼───────┐ │
│  │ Audio       │◀───│ MCP Bridge   │◀───│ Action        │ │
│  │ Response    │    │ Executor     │    │ Dispatcher    │ │
│  │ (TTS)       │    │              │    │               │ │
│  └─────────────┘    └──────────────┘    └────────┬───────┘ │
│                                                   │         │
│  ┌─────────────┐    ┌──────────────┐    ┌────────▼───────┐ │
│  │ Pi Agent    │◀───│ Intent       │    │ Visual        │ │
│  │ Integration │◀───│ Router       │    │ Feedback      │ │
│  │ (LLM)       │    │              │    │ (debug lines) │ │
│  └─────────────┘    └──────────────┘    └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 3. Core Components

### 3.1 AChimeraVoiceEntity (Main AI Actor)

**File:** `Source/Chimera/ProceduralGenerated/AI/VoiceEntity.h/.cpp`

The in-game AI entity the player interacts with. It's a visible actor (like DemoTerminal but more sophisticated) that:

- Has a visual mesh (terminal-like or abstract AI representation)
- Contains all subsystems as components
- Responds to voice commands via its Tick() loop (polling for new commands)
- Draws debug visualization when active
- Provides audio feedback (TTS responses)

**Key properties:**

```cpp
UPROPERTY() USoundCue* VoiceStartSound;      // Audio cue when listening
UPROPERTY() USoundCue* VoiceEndSound;        // Audio cue when done listening
UPROPERTY() UStaticMeshComponent* VoiceMesh;  // Visual representation
UPROPERTY() UTextRenderComponent* StatusDisplay; // Text display above entity

// Subsystem references (like DemoTerminal but extended)
UEconomyManager* EconomySystem;
UInventoryTradeComponent* TradeSystem;
UFactionComponent* FactionSystem;
USaveGameComponent* SaveSystem;
UMissionComponent* MissionSystem;
```

**Key methods:**

```cpp
void ProcessVoiceCommand(const FString& CommandText);  // Main entry point
FString ExecuteAction(const FVoiceAction& Action);      // Execute parsed action
void RespondWithAudio(const FString& ResponseText);     // TTS response
void DrawDebugVisualization();                          // Debug lines in Tick()
```

### 3.2 Voice Capture Component

**File:** `Source/Chimera/AI/VoiceCaptureComponent.h/.cpp`

Handles microphone input and audio preprocessing:

- Captures audio from system default device or specified mic
- Detects voice activity (VAD) to know when player starts/stops speaking
- Streams audio to STT engine
- Supports both real-time streaming and file-based input (for testing)

**Key properties:**

```cpp
UPROPERTY() bool bIsListening;
UPROPERTY() float SensitivityThreshold = 0.15f;
UPROPERTY() float SilenceTimeout = 1.5f;  // Seconds of silence to end utterance
```

### 3.3 Speech-to-Text (STT) Engine

**File:** `Source/Chimera/AI/SttEngine.h/.cpp`

Abstract STT interface with concrete implementations:

- **WhisperLocal**: Runs OpenAI Whisper locally (self-contained, no network needed)
- **AzureSTT**: Uses Azure Speech Services (higher quality, requires API key)
- **OpenAIWhisper**: Calls OpenAI's whisper API (good quality, requires API key)

**Key methods:**

```cpp
virtual FString TranscribeAudio(const TArray<uint8>& AudioData) = 0;
virtual FString TranscribeStream(TArray<uint8> Chunk);  // For streaming STT
```

### 3.4 Natural Language Parser

**File:** `Source/Chimera/AI/NlpParser.h/.cpp`

Parses natural language commands into structured actions:

- Pattern matching for simple commands ("spawn [actor] at [location]")
- Keyword extraction for medium complexity ("make the sky darker")
- LLM fallback for complex queries (delegated to Pi agent)

**Key structures:**

```cpp
USTRUCT()
struct FVoiceAction {
    GENERATED_BODY()
    
    EActionType Type;  // Spawn, Delete, ModifyProperty, Query, Economy, Mission, etc.
    FString Target;    // What to act on (actor name, property path)
    FVector Location;  // Where to spawn/move
    FVector Direction; // Direction for movement commands
    
    // Modification parameters
    float PropertyValue;  // Value to set
    FName PropertyName;   // Which property to modify
    
    // Query parameters
    FString QueryText;    // Free-text query for LLM fallback
};

enum class EActionType {
    SpawnActor,
    DeleteActor,
    MoveActor,
    ModifyProperty,
    QueryWorld,
    EconomyBuy,
    EconomySell,
    MissionAccept,
    SaveGame,
    LoadGame,
    Unknown  // Fallback to LLM
};
```

### 3.5 Action Dispatcher / MCP Bridge Executor

**File:** `Source/Chimera/AI/McpActionExecutor.h/.cpp`

Executes parsed actions via the existing MCP bridge:

- Maps VoiceActions to MCP bridge operations
- Handles actor spawning, property manipulation, console commands
- Returns results for audio feedback

**Key methods:**

```cpp
FString ExecuteSpawn(const FString& ActorClass, const FVector& Location);
FString ExecuteDelete(const FString& ActorName);
FString ExecuteModifyProperty(const FString& ObjectPath, FName Property, float Value);
FString ExecuteQuery(const FString& QueryText);
```

### 3.6 Text-to-Speech (TTS) Response System

**File:** `Source/Chimera/AI/TtsResponse.h/.cpp`

Generates audio responses for the player:

- Uses UE's built-in TTS if available, or delegates to external service
- Formats responses based on action type ("Spawned rock at location", "Credits updated")
- Supports both voice output and text display (StatusDisplay component)

### 3.7 Pi Agent Integration

**File:** `Source/Chimera/AI/PiAgentClient.h/.cpp`

Routes complex queries to the external Pi agent:

- Sends natural language queries to Pi via HTTP/WebSocket
- Receives structured responses with game actions
- Handles fallback when LLM can't determine intent

**Key methods:**

```cpp
FString QueryPi(const FString& UserQuery);
FVoiceAction ParsePiResponse(const FString& JsonResponse);
```

## 4. Integration Points

### 4.1 MCP Bridge (Existing)

The MCP bridge already provides all the heavy lifting:

- `spawn_actor` / `spawn_blueprint` — spawn actors with transform
- `set_object_property` / `get_object_property` — modify game state
- `console_command` — execute UE console commands
- `delete_actor` / `duplicate_actor` — manipulate world

**Integration:** The Voice entity calls MCP bridge operations directly via its existing HTTP/WebSocket endpoints. No new bridge handlers needed for basic functionality.

### 4.2 DemoTerminal (Existing)

DemoTerminal already has economy/trade/save/mission exec commands:

- `DemoStatus()`, `DemoBuy()`, `DemoSell()`, `DemoSave()`, `DemoLoad()`, `DemoMission()`

**Integration:** The Voice entity wraps these existing commands with voice access. No need to duplicate logic — just add a new command layer on top.

### 4.3 Input System (Existing)

Current input bindings: WASD/mouse movement, jump/crouch/interact/drop.

**Extension needed:** Add a "voice activation" key binding (e.g., V or Tab hold-to-talk) that triggers the Voice Capture Component when pressed.

## 5. Command Examples

### Simple Commands

```
Player: "Spawn a rock here"
Voice: [processes] → spawns SM_Rock at player location
Response: "Rock spawned."

Player: "Delete that rock"
Voice: [processes] → deletes nearest rock actor
Response: "Rock deleted."
```

### Property Modification

```
Player: "Make the sky darker"
Voice: [parses intent] → modifies SkySphere material brightness property
Response: "Sky brightness reduced to 0.3."

Player: "Set gravity to zero"
Voice: [processes] → sets CharacterMovement GravityScale to 0.0
Response: "Gravity disabled."
```

### Economy/Mission (via DemoTerminal)

```
Player: "Buy 100 titanium"
Voice: [routes to DemoTerminal.DemoBuy(100)]
Response: "Purchased 100 Titanium for 10000 credits."

Player: "Accept the delivery mission"
Voice: [routes to DemoTerminal.DemoMission()]
Response: "Accepted Delivery_Titanium_Batch_1. Deliver 500 Titanium to Orbital_Hub_7."
```

### LLM-Enhanced Queries (Pi Agent)

```
Player: "What can I do in this game?"
Voice: [routes to Pi agent] → LLM generates list of available commands
Response: "You can spawn objects, modify the environment, trade commodities, accept missions, and save/load your progress. Try 'spawn a rock' or 'buy titanium'."

Player: "Show me all the actors in this level"
Voice: [routes to Pi agent] → LLM generates query for actor count + list
Response: "There are 47 actors in this level. Would you like me to highlight them?"
```

## 6. Implementation Phases

### Phase 1: Voice Command Foundation (No STT/TTS)

- Create `AChimeraVoiceEntity` with visual mesh and debug visualization ✅ DONE
- Add console command interface for voice commands (bypass STT initially) ✅ DONE
- Integrate with existing DemoTerminal exec commands ✅ DONE
- Test via text input (`ke <VoiceEntity> VoiceCommand "spawn a rock here"`) ✅ DONE

### Phase 2: Speech-to-Text Integration

- Implement `SttEngine` interface with WhisperLocal backend
- Add voice capture component (microphone input)
- Integrate STT pipeline into Voice entity's Tick loop
- Test voice commands end-to-end (speech → text → action)

### Phase 3: Text-to-Speech & Audio Feedback

#### 3.1 Quick Start: UE5 Built-In TTS Plugin

- Enable UE5's experimental `TextToSpeech` plugin (uses CMU Flite)
- Zero integration effort; works out of the box in UE5.8
- Blueprint API: `Get TextToSpeechEngineSubsystem → Add Default Channel → Activate Channel → Speak on Channel`
- **Pros**: Immediate feedback, no external dependencies
- **Cons**: Robotic/low-quality speech; limited to English; single built-in voice

#### 3.2 Production Path: Qwen3-TTS + CrispASR C-ABI

**Model**: `qwen3-tts-12hz-1.7b-voicedesign-q8_0.gguf` (1.9 GB, recommended quantized)
**Runtime**: CrispASR v0.8.3+ with Qwen3-TTS backend
**License**: Apache-2.0 (compatible with commercial use)

##### Integration Architecture

```
[Player speaks / text input]
        |
        v
[CrispASR C-ABI via UE5 Plugin DLL]
  - crispasr_session_open("qwen3-tts-1.7b-voicedesign")
  - crispasr_session_synthesize(text) → float32* PCM @ 24kHz
  - crispasr_session_close()
        |
        v
[Audio Conversion Layer]
  - Resample 24kHz → 48kHz (UE5 engine default)
  - Convert float32 → int16
  - Pack into TArray<uint8>
        |
        v
[USoundWave Creation]
  - NewObject<USoundWave>()
  - Populate RawData with PCM buffer
  - Set SampleRate, NumSamples, Channels
        |
        v
[UAudioComponent Playback]
  - CreateComponentByClass<UAudioComponent>
  - SetSound(soundWave)
  - Play() / Stop()
```

##### Windows Build Path

1. **Download prebuilt CrispASR**: `crispasr-windows-x86_64-cpu-legacy.zip` from GitHub releases
2. **Download Qwen3-TTS model**: `huggingface-cli download cstr/qwen3-tts-1.7b-voicedesign-GGUF`
3. **Download tokenizer**: `huggingface-cli download cstr/qwen3-tts-tokenizer-12hz-GGUF`
4. **Create UE5 plugin module** that wraps CrispASR C-ABI
5. **Link against prebuilt DLLs**; no compilation needed for Windows
6. **Deploy as part of game content** (models stored in Content/ directory)

##### Alternative: Build from Source (Optional)

CrispASR provides `build-windows.bat` that:

1. Locates Visual Studio 2022 via `vswhere.exe`
2. Calls `vcvars64.bat` to initialize MSVC environment
3. Runs CMake with Ninja generator
4. Outputs `build\bin\crispasr.exe`

##### Voice Design Feature

The VoiceDesign variant generates speech from natural language instructions:

```bash
crispasr \
    --backend qwen3-tts-1.7b-voicedesign \
    -m auto \
    --instruct "A young female voice with a slight British accent, energetic" \
    --tts "Hello, I am an excited engineer." \
    --tts-output hello.wav
```

This means we can describe the Voice entity's personality in-game:

- **Helpful assistant**: "A calm, professional female voice with a slight American accent"
- **Playful companion**: "An energetic young male voice with a British accent, slightly fast-paced"
- **Mysterious AI**: "A deep, resonant male voice with a neutral tone, measured pace"

### Phase 4: Pi Agent Integration

- Implement `PiAgentClient` for LLM-enhanced queries
- Add fallback routing from NLP parser to Pi agent
- Test complex natural language queries
- Document available commands and capabilities

## 7. Technical Considerations

### Performance

- STT processing should run on a separate thread to avoid blocking game Tick()
- TTS responses can be pre-cached for common phrases
- Debug visualization only active when player is near Voice entity (<800 units)

### Security

- MCP bridge already has security filtering (blocks dangerous commands)
- Voice commands inherit same security constraints
- No ability to execute arbitrary code or crash the game via voice

### Modularity

- STT backend is swappable (WhisperLocal ↔ AzureSTT ↔ OpenAIWhisper)
- NLP parser can be extended with new pattern rules
- Pi agent integration is optional (works without LLM for basic commands)

## 8. Files to Create/Modify

### New Files

```
Source/Chimera/ProceduralGenerated/AI/VoiceEntity.h/.cpp      # Main AI actor
Source/Chimera/AI/VoiceCaptureComponent.h/.cpp                # Mic input
Source/Chimera/AI/SttEngine.h/.cpp                            # STT interface + WhisperLocal
Source/Chimera/AI/NlpParser.h/.cpp                            # NLP parser
Source/Chimera/AI/McpActionExecutor.h/.cpp                    # MCP bridge executor
Source/Chimera/AI/TtsResponse.h/.cpp                          # TTS response system
Source/Chimera/AI/PiAgentClient.h/.cpp                        # Pi agent integration
```

### Modified Files

```
Config/DefaultInput.ini                                       # Add voice activation key binding
Source/Chimera/ProceduralGenerated/Demo/DemoPlayerController.cpp  # Add voice command delegation
Chimera.Build.cs                                            # Add STT library dependencies (whisper.cpp, etc.)
```

## 9. Risks & Traps

| Risk | Mitigation |
| ------ | ----------- |
| STT latency blocks gameplay | Run STT on separate thread; show "processing" indicator |
| WhisperLocal too heavy for game thread | Use async processing; pre-load model to memory once |
| Voice commands misinterpreted | Pattern matching first, LLM fallback second; always confirm ambiguous actions |
| MCP bridge security bypassed | Inherit existing security filters; no new exec paths without validation |
| Audio feedback disrupts gameplay | Make TTS optional; default to text-only for testing |
