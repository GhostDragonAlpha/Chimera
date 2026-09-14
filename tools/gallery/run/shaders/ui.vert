#version 450
// THE ENGINE STUDIO — overlay quad vertex shader (pixel-space UI, no camera)
layout(location = 0) in vec2 in_pos;   // pixel coords, origin top-left
layout(location = 1) in vec2 in_uv;
layout(location = 2) in vec4 in_col;
layout(location = 3) in float in_flags; // 0 = font coverage (D1), 1 = reel thumbnail RGBA (D3)

layout(push_constant) uniform PC { vec2 screen; } pc;

layout(location = 0) out vec2 uv;
layout(location = 1) out vec4 col;
layout(location = 2) out float flags;

void main() {
    vec2 ndc = (in_pos / pc.screen) * 2.0 - 1.0;
    gl_Position = vec4(ndc.x, ndc.y, 0.0, 1.0);
    uv    = in_uv;
    col   = in_col;
    flags = in_flags;
}
