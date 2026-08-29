#version 450
// THE ENGINE STUDIO — overlay quad fragment shader.
// The font atlas is R8: glyph cells hold coverage; cell 95 (DEL slot) is a
// solid-white texel block so colored rects are the same draw call as text.
layout(set = 0, binding = 0) uniform sampler2D font_tex;

layout(location = 0) in vec2 uv;
layout(location = 1) in vec4 col;
layout(location = 0) out vec4 out_col;

void main() {
    float a = texture(font_tex, uv).r;
    out_col = vec4(col.rgb, col.a * a);
}
