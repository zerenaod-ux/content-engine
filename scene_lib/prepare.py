"""Consume browser-measured local SVG bounds and recompute camera framing."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scene_lib.writer import auto_camera

if __name__ == '__main__':
    path = Path(sys.argv[1]); spec = json.loads(path.read_text())
    spec['_path_bounds'] = json.load(sys.stdin)
    auto_camera(spec)
    path.write_text(json.dumps(spec, indent=1, ensure_ascii=False))
