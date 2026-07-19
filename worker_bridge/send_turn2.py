#!/usr/bin/env python3
"""Send 10 main questions to the worker and wait for answers."""
import json
import time
import urllib.request

WORKER_URL = "http://127.0.0.1:8890"

# Main's 10 questions for the Worker (Round 2, Phase B)
questions = [
    "Given radix sort at 62% of frame time, would a hybrid CPU/GPU approach (CPU bins into coarse 2D grid, then GPU sorts per-bin) reduce latency at the cost of increased CPU work — and what splat count makes that crossover worthwhile?",
    "The 8-level MIP bucket system for density culling — have you considered a continuous (non-bucketed) approach where each Gaussian contributes a fractional weight based on exact footprint overlap ratio, trading compute for smoother LOD transitions?",
    "The 0.3 hysteresis in temporal normalization is a global constant across all tiles — could a per-tile adaptive hysteresis (based on local motion vectors from the previous frame) reduce the 8.2 delta-E during fast pans?",
    "Float16 for SH band-2 gives >48 dB PSNR — have you tested band-3 SH (16 coefficients instead of 9) at float16 and measured the accuracy regression, or is the architectural limit hard at 3 bands?",
    "The procedural detail mipmap uses tile-coordinate seeded noise — does this produce visible tiling artifacts at the 0.3 px/Gaussian cutoff boundary, and have you tested a screen-space derivative noise function as an alternative?",
    "Hash collision rate at 0.003% is low — but the covariance-determinant tie-breaker assumes the two colliding Gaussians have different determinants. What happens when they are clones (identical position, scale, rotation)?",
    "Adaptive tile-grid coarsening under-utilizes tiles below 10% — does the merged 2×2 tile reduce sort efficiency for the merged group, potentially creating a new hotspot in the larger tile?",
    "The 3-sigma seam at 0.01 world units is deferred — but 0.5% of frames with visible discontinuity means roughly 1 in 200 frames has an artifact. What is the perceptual impact measured in terms of viewer-reported 'hitches' per minute?",
    "Viewpoint-dependent culling causes 70% of >5% count variance — is there a frame-to-frame coherence heuristic that could reduce this by retaining Gaussians that were visible in the previous frame even if they pass the density cap?",
    "The manifest is stored in the DNA graph as a FeatureUpdate node — does the Spiral loop versioning of the manifest interact correctly with the compaction heuristic that archives old FeatureUpdate nodes, or can a stale manifest survive compaction?",
]

# Prior Q&A context (abbreviated)
qa_context = """Round 1 Q&A (Worker asked, Main answered):
1. GPU pipeline: compute radix sort + fragment alpha blend. CPU cull dominates below 100K.
2. Sorting bottleneck ~62% at 600K, alpha ~28%.
3. Density cap: pre-sort decimation by projected area, 8 MIP buckets.
4. Temporal normalization: 0.3 hysteresis lerp, ~3 frame recovery.
5. Float16 baking: 64-byte struct, SH band-2 at >48 dB PSNR.
6. Detail injection at 0.3 px/Gaussian: pre-baked mipmap, tile-coordinate seeded noise.
7. Testing: SSIM 0.97 threshold, deterministic hash pre-sort.
8. Profiling: GPU timestamps per dispatch, tile utilization histogram.
9. In-Gaussian camera: 0.01 world unit clamp, <0.1% frames affected.
10. Pipeline: manifest JSON, postflight gate validates within 5%."""

prompt_text = f"""You are a lead engineer answering 10 questions about the Gaussian splatting system.

PREVIOUS Q&A CONTEXT (what has already been discussed):
{qa_context}

THE 10 QUESTIONS TO ANSWER:
{' '.join(f'{i+1}. {q}' for i, q in enumerate(questions))}

INSTRUCTIONS:
- Answer each question thoroughly and technically.
- Reference actual code paths, algorithms, and tradeoffs.
- Be honest about unknowns.
- Return a numbered list of 10 answers.
"""

body = json.dumps({"message": prompt_text})
req = urllib.request.Request(
    f"{WORKER_URL}/api/prompt",
    data=body.encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=120) as resp:
    print("Sent. Result:", resp.read().decode())

print("\nWaiting for worker to complete...")
time.sleep(5)

# Poll until settled
for i in range(30):
    try:
        resp = urllib.request.urlopen(f"{WORKER_URL}/api/get_state", timeout=5)
        state = json.loads(resp.read().decode())
        streaming = state.get("data", {}).get("isStreaming", True)
        if not streaming:
            print(f"Settled after ~{i*3+5}s")
            break
    except Exception as e:
        print(f"  poll error: {e}")
    time.sleep(3)
else:
    print("Timed out waiting for settle")

# Get worker's answers
resp = urllib.request.urlopen(f"{WORKER_URL}/api/get_messages", timeout=5)
msgs = json.loads(resp.read().decode())
messages = msgs.get("data", {}).get("messages", [])
for m in reversed(messages):
    if m.get("role") == "assistant" and m.get("content"):
        text = m["content"]
        if isinstance(text, list):
            for seg in text:
                if seg.get("type") == "text":
                    print("\n=== WORKER'S ANSWERS ===\n")
                    print(seg["text"][:4000])
        else:
            print("\n=== WORKER'S ANSWERS ===\n")
            print(text[:4000])
        break
