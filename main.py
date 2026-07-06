from pathlib import Path
import moderngl_window as mglw
from imgui_bundle import imgui
from moderngl_window.integrations.imgui_bundle import ModernglWindowRenderer
import moderngl
from constants import BASE_DIR,USER_DIR, VERTEX_SHADER
from shader_meta import parse_metadata

class App(mglw.WindowConfig):
    gl_version = (4, 1)
    title = "GLSL Viewer"
    aspect_ratio = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shader_files = sorted(USER_DIR.glob("*.frag"))
        self.current_index = 0
        self.frag_path = self.shader_files[self.current_index]
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
        self.ini_path = str(USER_DIR.parent / "imgui.ini")
        imgui.get_io().set_ini_filename(self.ini_path)
        self.show_ui = True
        for name in self.program:
            member = self.program[name]
            if isinstance(member, moderngl.Uniform):
                print(name, member, member.fmt)
        self.my_time = 0.0
        self.time_speed = 1.0
        self.paused = False
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
        names = [f.name for f in self.shader_files]
        changed, self.current_index = imgui.combo("shader", self.current_index, names)
        if changed:
            self.frag_path = self.shader_files[self.current_index]
            self.last_mtime = self.frag_path.stat().st_mtime
            self.reload_shader()
        if imgui.button("Rescan"):                                   
            self.shader_files = sorted(USER_DIR.glob("*.frag"))
        _, self.paused = imgui.checkbox("pause", self.paused)
        imgui.same_line()
        if imgui.button("reset"):
            self.my_time = 0.0
        _, self.time_speed = imgui.slider_float("speed", self.time_speed, 0.0, 3.0)
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
        if not self.paused:
            self.my_time += frametime * self.time_speed
        mtime = self.frag_path.stat().st_mtime
        if mtime != self.last_mtime:
            self.last_mtime = mtime
            self.reload_shader()
        self.ctx.clear(0.0, 0.0, 0.0)
        self.apply_uniforms()       
        if "u_time" in self.program:
            self.program["u_time"].value = self.my_time
        if "u_resolution" in self.program:
            self.program["u_resolution"].value = self.wnd.buffer_size           
        self.quad.render(self.program)
        imgui.new_frame()
        if self.show_ui:
            imgui.set_next_window_size((400, 500), imgui.Cond_.first_use_ever)
            imgui.begin("Controls")
            self.draw_ui()               
            imgui.end()
        imgui.render()
        self.imgui.render(imgui.get_draw_data())
    
    def on_resize(self, width: int, height: int):
        self.ctx.viewport = (0, 0, *self.wnd.buffer_size)
        self.imgui.resize(width, height)

    def on_key_event(self, key, action, modifiers):
        self.imgui.key_event(key, action, modifiers)
        if imgui.get_io().want_capture_keyboard:
            return
        if action == self.wnd.keys.ACTION_PRESS and key == self.wnd.keys.TAB:
            self.show_ui = not self.show_ui
        if action == self.wnd.keys.ACTION_PRESS and key == self.wnd.keys.F and modifiers.ctrl:
            self.wnd.fullscreen = not self.wnd.fullscreen

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