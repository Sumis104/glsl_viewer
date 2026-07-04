#version 410

in vec2 v_uv;
out vec4 fragColor;
uniform vec3 u_color;   // default: 0.2 0.8 1.0
uniform float u_test;   // default: 0.5 range: 0.0 3.0
uniform vec2 u_offset;  // default: 0.1 0.2
uniform int u_count;    // default: 3 range: 1 8
uniform float u_time;
void main() {
    vec2 uv = v_uv + u_offset;                    // offsetで絵がずれる
    float wave = sin(uv.x * float(u_count) * 6.2831) * 0.5 + 0.5;   // countで縞の本数
    vec3 grad = vec3(uv, wave) ;
    float pulse = sin(u_time) * 0.5 + 0.5;
    fragColor = vec4(grad * u_color * pulse, 1.0);
}