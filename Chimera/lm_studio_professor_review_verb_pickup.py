import json
import urllib.request

url = "http://localhost:1234/v1/chat/completions"

body = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [
        {
            "role": "system",
            "content": "You are the Professor for the Chimera Project's Ralph Loop. Your task is to review research summaries for features and assign a grade (A, B, C, or F) based on the quality, completeness, and fidelity to references and parameters. Provide the grade letter, a score (0-100), and the reasoning sentence. Format your response as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        },
        {
            "role": "user",
            "content": "RESEARCH SUMMARY FOR LOOP 2 BASIC VERBS FEATURE - Verb_PickUp (interaction):\n\nLoop 2 — Basic Verbs:\n- Verb_PickUp (interaction)\n\nResearch summary extracted parameters for UE5 pickup/interaction system architecture:\n\n1. Interaction Component Patterns:\n   - UInteractComponent or custom InteractionComponent attached to player character\n   - Proximity-based triggers using UPrimitiveComponent::OnComponentBeginOverlap and OnComponentEndOverlap\n   - Input action bindings for \"Interact\" (typically mapped to E key or gamepad button)\n\n2. Pickup Actor Patterns:\n   - APickupActor base class extending AActor\n   - Components: USceneComponent (root), UStaticMeshComponent or USkeletalMeshComponent, collision component\n   - State transitions: Ready → Interacting → Completed/PickedUp\n\n3. Proximity Trigger Parameters:\n   - Interaction radius: typically 200-300 cm (150-250 Unreal units) for pickup interactions\n   - Trace type: line trace or sphere overlap from player camera/pawn location\n   - Input action: \"Interact\" mapped to keyboard 'E' or gamepad 'X/A' button\n\n4. State Machine Transitions:\n   - Ready: Actor is within interaction radius, prompt visible\n   - Interacting: Player pressed interact button, animation/transition playing\n   - Completed: Item added to inventory, actor destroyed or marked as picked up\n\nPlease review this research summary and assign a grade (A, B, C, or F), a score (0-100), and provide the exact reasoning sentence. Format your response as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        }
    ],
    "temperature": 0.1,
    "max_tokens": 500
}

req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    response = urllib.request.urlopen(req)
    response_data = response.read().decode('utf-8')
    print(response_data)
except Exception as e:
    print(f"Error: {e}")
