#version 410

in vec2 v_uv;
out vec4 fragColor;
uniform vec3 u_color;
uniform float u_test;
void main() {
    vec3 grad = vec3(v_uv.x, v_uv.y, 0.5);
    u_color = vec3(1.0, 0.5, 0.2); // This line is added to modify the uniform color
    fragColor = vec4(grad * u_color + u_test * 0.001, 1.0);
}