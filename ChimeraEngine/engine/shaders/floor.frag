#version 450
// floor.frag — the plane's ink: flat color, NO lighting. A lit floor is a
// second scene to keep coherent; this is the canvas the contact shadow needs:
// ~55/255 — light enough that black@0.38 leaves a visible ~21/255 delta
// (above the perception floor), dark enough not to compete with the subject.
// The shadow (no depth write) blends over this; the mesh's depth-tested draw
// wins where they overlap.
layout(location = 0) out vec4 fragColor;
void main() {
    fragColor = vec4(55.0 / 255.0, 55.0 / 255.0, 55.0 / 255.0, 1.0);
}
