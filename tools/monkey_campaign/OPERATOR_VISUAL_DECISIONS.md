# Mandatory visual presentation for human decisions

Captain's workflow ruling, 2026-09-27. A human decision is not pending merely
because an artifact exists somewhere on disk. The Lieutenant must present the
decision to the Captain in the active conversation before an answer can exist.

## Presentation gate

Any decision whose answer depends on appearance, orientation, labeling, motion,
camera framing, gameplay feel or a visual comparison requires a visual decision
packet and an in-chat presentation. A path, hash, report, mailbox notice or request
to open a local file does not satisfy this gate. Workers prepare evidence; the
Lieutenant presents it. The Sergeant routes the packet and continues unrelated work.

For anatomical or other spatial-semantic questions, first run the semantic-frame
procedure in [Semantic 3D verification](../../docs/SEMANTIC_3D_VERIFICATION.md).
Geometry, independent domain claims, topology, ports and a physical witness should
determine the direction when the evidence exists. A screenshot is then a debugging
view of those facts. If the semantic packet refuses because required anatomy is
missing, state that limitation; do not ask a model to guess. The Captain may still
make an explicit authored convention choice, but its receipt must call it authored
semantics rather than biological inference.

The packet must contain:

- the task ID, exact source/build/head and decision ID;
- one short neutral question and every lawful answer, including `CANNOT DECIDE`
  when the evidence can genuinely be inconclusive;
- side-by-side or sequential labeled images for every visual choice, plus a clean
  view when diagnostic labels obscure the subject;
- camera angle/orientation, target, distance, projection/FOV, clipping, resolution
  and state/tick identity sufficient to reproduce each view;
- the physical or product consequence of each answer and what remains unchanged;
- capture and manifest hashes and the evidence location;
- a falsifier: what visible defect would make the packet unusable.

Do not encode the preferred answer through misleading scale, crop, lighting, color,
ordering or prose. Use the same state and comparable cameras when alternatives are
spatially comparable. Show relevant context and a close-up. If static images cannot
answer a motion or interaction question, present a playable run or video; do not ask
the Captain to infer motion from a still.

## Lieutenant procedure

During an operator-triggered lead session, the Lieutenant checks current task
messages, suggestion-box questions and the Sergeant mailbox for decision packets.
For each ready packet:

1. Verify the referenced bytes and inspect the actual image/video. Refuse a broken,
   stale, clipped, illegible or one-sided packet and return a concrete correction.
2. Display the actual evidence inline in the Captain's conversation. For two or
   more images, label them exactly as the answer choices and present them together
   when the client permits. State the question, choices and consequences in plain
   language. Do not merely provide a filesystem path.
3. Ask for one explicit answer. Silence, elapsed time, a model recommendation or an
   earlier answer to a materially different image is not consent.
4. After the Captain answers, write a decision receipt bound to the shown packet:
   decision ID, answer, Captain message reference/time, presenter identity, source
   identities, image/video and manifest hashes, and the exact choice wording.
5. Route that receipt to the blocked card. Independent review verifies the binding.
   Only then may the answer satisfy a human-decision clause.

The Lieutenant may give a recommendation, clearly labeled as such, after showing
the evidence. The recommendation is never recorded as the Captain's answer. If the
Captain says the evidence is inadequate, record `CANNOT DECIDE` and improve the
instrument or views; never convert it to A/B/yes/no.

Nonvisual architectural, financial or policy choices use the same procedure with a
compact comparison table instead of invented imagery. Irreversible external actions
still follow their normal approval requirements.

## Scheduling and grading

A card waiting for a presented human answer is `DECISION_BLOCKED`, not failed,
complete or actively implemented. Its worker checkpoints and releases the slot;
the fleet continues other eligible cards. Do not keep a worker or GPU busy while
waiting for the Captain. The Sergeant includes ready decision packets in its next
mail to the Lieutenant and does not repeatedly notify unchanged packets.

The absence of an operator answer is an external gate, not a model-quality defect.
A worker is graded on whether it prepared an accurate, usable packet and routed it.
A lead is graded on whether it actually presented the packet and bound the response.
No model receives credit for choosing on the Captain's behalf.

## Minimum receipt fields

The accepted task contribution stores these fields in its existing evidence format;
this ruling does not create a second scheduler or database:

`decision_id`, `task_id`, `question`, `choices`, `answer`,
`captain_message_reference`, `presented_by`, `presented_at_utc`,
`source_head`, `capture_sha256`, `manifest_sha256`, and `packet_reference`.

Missing fields, a changed capture hash, unshown evidence, or an agent-authored human
answer fires the gate. Preserve superseded packets and answers as history rather
than silently editing them.
