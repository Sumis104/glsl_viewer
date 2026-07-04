#version 410

in vec2 v_uv;
out vec4 fragColor;
uniform vec3 u_color;   // default: 1.0 1.0 1.0

void main() {
    vec3 grad = vec3(v_uv.x, v_uv.y, 0.5);
    fragColor = vec4(grad * u_color, 1.0);
}