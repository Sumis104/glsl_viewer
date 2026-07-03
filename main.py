from pathlib import Path
import moderngl_window as mglw
import sys
from imgui_bundle import imgui
from moderngl_window.integrations.imgui_bundle import ModernglWindowRenderer

import moderngl

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)   # PyInstaller展開先
else:
    BASE_DIR = Path(__file__).parent

VERTEX_SHADER = """
#version 410
in vec3 in_position;
in vec2 in_texcoord_0;
out vec2 v_uv;
void main() {
    gl_Position = vec4(in_position, 1.0);
    v_uv = in_texcoord_0;
}
"""

class App(mglw.WindowConfig):
    gl_version = (4, 1)
    title = "GLSL Viewer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        frag_path = BASE_DIR / "shaders" / "test.frag"
        frag_source = frag_path.read_text()
        self.program = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=frag_source,
        )
        self.quad = mglw.geometry.quad_fs()
        imgui.create_context()
        imgui.get_io().font_global_scale = 2.25
        self.imgui = ModernglWindowRenderer(self.wnd)
        self.show_ui = True
        for name in self.program:
            member = self.program[name]
            if isinstance(member, moderngl.Uniform):
                print(name, member, member.fmt)
        self.build_uniforms()
    
    def build_uniforms(self):
        self.uniforms = {} 
        for name in self.program:
            member = self.program[name]
            if isinstance(member, moderngl.Uniform):
                if name in{"u_time", "u_resolution"}:
                    continue
                self.uniforms[name] = {   
                    "fmt": member.fmt,
                    "value": member.value,
                }

    def draw_ui(self):
        for name, info in self.uniforms.items():   # キーと値を同時に取り出す
            if info["fmt"] == "3f":
                changed, new_value = imgui.color_edit3(name, info["value"])
                info["value"] = new_value
            elif info["fmt"] == "1f":
                changed, new_value = imgui.slider_float(name, info["value"], 0.0, 1.0)
                info["value"] = new_value

    def apply_uniforms(self):
        for name, info in self.uniforms.items():
            self.program[name].value = info["value"]

    def on_render(self, time, frametime):
        self.ctx.clear(0.0, 0.0, 0.0)
        self.apply_uniforms()               # 台帳→GPU
        self.quad.render(self.program)
        imgui.new_frame()
        if self.show_ui:
            imgui.begin("Controls")
        self.draw_ui()                  # 台帳→GUI→台帳
        imgui.end()
        imgui.render()
        self.imgui.render(imgui.get_draw_data())
    
    def on_resize(self, width: int, height: int):
        self.imgui.resize(width, height)

    def on_key_event(self, key, action, modifiers):
        self.imgui.key_event(key, action, modifiers)
        if action == self.wnd.keys.ACTION_PRESS and key == self.wnd.keys.TAB:
            self.show_ui = not self.show_ui

    def on_mouse_position_event(self, x, y, dx, dy):
        self.imgui.mouse_position_event(x, y, dx, dy)

    def on_mouse_drag_event(self, x, y, dx, dy):
        self.imgui.mouse_drag_event(x, y, dx, dy)

    def on_mouse_scroll_event(self, x_offset, y_offset):
        self.imgui.mouse_scroll_event(x_offset, y_offset)

    def on_mouse_press_event(self, x, y, button):
        self.imgui.mouse_press_event(x, y, button)

    def on_mouse_release_event(self, x: int, y: int, button: int):
        self.imgui.mouse_release_event(x, y, button)

    def on_unicode_char_entered(self, char):
        self.imgui.unicode_char_entered(char)

    


if __name__ == "__main__":
    App.run()