from pathlib import Path
import moderngl_window as mglw
import sys
from imgui_bundle import imgui
from moderngl_window.integrations.imgui_bundle import ModernglWindowRenderer
import moderngl
import re

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

def parse_metadata(source):
    meta = {}
    for line in source.splitlines():   # ← リスト手書きじゃなくファイル全文から
        m = re.search(r'uniform\s+\w+\s+(\w+)', line)
        if not m:
            continue
        name = m.group(1)

        d = re.search(r'default:\s*([-\d.\s]+)', line)
        nums = []
        if d:
            nums = [float(x) for x in re.findall(r'[-\d.]+', d.group(1))]

        # ここから追加: range対応
        r = re.search(r'range:\s*([-\d.]+)\s+([-\d.]+)', line)
        range_val = None
        if r:
            range_val = (float(r.group(1)), float(r.group(2)))

        meta[name] = {"default": nums, "range": range_val}
    return meta


class App(mglw.WindowConfig):
    gl_version = (4, 1)
    title = "GLSL Viewer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.frag_path = BASE_DIR / "shaders" / "test.frag"
        self.frag_source = self.frag_path.read_text()
        self.last_mtime = self.frag_path.stat().st_mtime
        self.program = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=self.frag_source,
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
        
    def reload_shader(self):
        try:
            source = self.frag_path.read_text()
            program = self.ctx.program(
                vertex_shader=VERTEX_SHADER,
                fragment_shader=source,
            )
        except Exception as e:
            print("COMPILE ERROR:", e)
            return
        self.frag_source = source
        self.program = program
        self.build_uniforms()
    
    def build_uniforms(self):
        meta = parse_metadata(self.frag_source)      # ★追加1: パース結果を先に取っておく
        self.uniforms = {}
        for name in self.program:
            member = self.program[name]
            if isinstance(member, moderngl.Uniform):
                if name in {"u_time", "u_resolution"}:
                    continue
                info = {                              # ★変更: 辞書に一旦名前をつける
                "fmt": member.fmt,
                "value": member.value,
                }
                if name in meta:                      # ★追加2: metaにこの名前があれば上書き
                    nums = meta[name]["default"]
                    if len(nums) == 1:
                        if info["fmt"] == "1i":
                            info["value"] = int(nums[0])
                        else:
                            info["value"] = nums[0]
                    elif len(nums) > 1:
                        info["value"] = tuple(nums)
                    if meta[name]["range"]:
                        info["range"] = meta[name]["range"]
                self.uniforms[name] = info            # ★最後にinfoを登録


    def draw_ui(self):
        for name, info in self.uniforms.items():
            if info["fmt"] == "3f":
                changed, new_value = imgui.color_edit3(name, info["value"])
                info["value"] = new_value
            elif info["fmt"] == "1f":
                lo, hi = info.get("range", (0.0, 1.0))
                changed, new_value = imgui.slider_float(name, info["value"], lo, hi)
                info["value"] = new_value
            elif info["fmt"] == "2f":
                lo, hi = info.get("range", (0.0, 1.0))
                changed, new_value = imgui.slider_float2(name, info["value"], lo, hi)
                info["value"] = tuple(new_value)
            elif info["fmt"] == "1i":
                lo, hi = info.get("range", (0, 10))
                changed, new_value = imgui.slider_int(name, info["value"], int(lo), int(hi))
                info["value"] = new_value


    def apply_uniforms(self):
        for name, info in self.uniforms.items():
            self.program[name].value = info["value"]

    def on_render(self, time, frametime):
        mtime = self.frag_path.stat().st_mtime
        if mtime != self.last_mtime:
            self.last_mtime = mtime
            self.reload_shader()
        self.ctx.clear(0.0, 0.0, 0.0)
        self.apply_uniforms()       
        if "u_time" in self.program:
            self.program["u_time"].value = time       
        self.quad.render(self.program)
        imgui.new_frame()
        if self.show_ui:
            imgui.begin("Controls")
            self.draw_ui()               
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