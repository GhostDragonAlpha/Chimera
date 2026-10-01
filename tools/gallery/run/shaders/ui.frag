#version 450
// THE ENGINE STUDIO — overlay quad fragment shader.
// One atlas image, two read modes (D3):
//   flags 0 — font cells: alpha channel holds coverage; cell 95 (DEL slot) is a
//             solid-white block so colored rects are the same draw call as text.
//   flags 1 — reel thumbnails: straight RGBA from the capture, tinted by col.
layout(set = 0, binding = 0) uniform sampler2D font_tex;

layout(location = 0) in vec2 uv;
layout(location = 1) in vec4 col;
layout(location = 2) in float flags;
layout(location = 0) out vec4 out_col;

void main() {
    vec4 tex = texture(font_tex, uv);
    out_col = flags > 0.5 ? tex * col
                          : vec4(col.rgb, col.a * tex.a);
}
