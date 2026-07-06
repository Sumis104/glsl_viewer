import sys
from pathlib import Path
import shutil

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)   # PyInstaller展開先
else:
    BASE_DIR = Path(__file__).parent
USER_DIR = Path.home() / "Documents" / "GLSLViewer" / "shaders"
if not USER_DIR.exists():
    USER_DIR.mkdir(parents=True)
    shutil.copy(BASE_DIR / "shaders" / "test.frag", USER_DIR / "test.frag")

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