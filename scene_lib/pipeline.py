"""Content-addressed accepted stages and last rejected candidate; no credentials stored."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fingerprint(stage='scene'):
    if stage == 'plan':
        import inspect
        from scene_lib.writer import plan_prompt, check_plan, normalize_plan, timeline, STAGE_TEXT, DURATION
        source=(''.join(inspect.getsource(f) for f in (plan_prompt,check_plan,normalize_plan,timeline))+STAGE_TEXT+str(DURATION)).encode()
        return hashlib.sha256(source+(ROOT/'scene_lib/catalog.py').read_bytes()).hexdigest()
    return hashlib.sha256(b''.join((ROOT / p).read_bytes() for p in (
        'scene_lib/writer.py', 'scene_lib/validate.py', 'scene_lib/evidence.py',
        'scene_lib/catalog.py', 'scene_lib/scene.html', 'scene_lib/pipeline.py',
        'scene_lib/example_flow.json', 'scene_lib/example_icons.json'))).hexdigest()


class StageCache:
    def __init__(self, topic):
        key = hashlib.sha256(topic.strip().encode()).hexdigest()
        self.path = Path(os.environ.get('CE_CACHE_DIR', '.ce-cache')) / key

    def accepted(self, stage, checker):
        try:
            entry = json.loads((self.path / (stage + '.json')).read_text())
            if entry.get('fingerprint') != fingerprint(stage): return None
            value=entry['value']
            return value if not checker(value) else None
        except (OSError, ValueError, TypeError, KeyError):
            return None

    def save(self, stage, value):
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path / (stage + '.json')).write_text(json.dumps({'fingerprint':fingerprint(stage),'value':value}, ensure_ascii=False))


def save_attempt(stage, candidate, errors):
    path = Path('attempts'); path.mkdir(exist_ok=True)
    # bounded: only latest repair candidate per stage, kept on failed workflow too
    (path / (stage + '.json')).write_text(json.dumps({'candidate': candidate, 'errors': errors}, ensure_ascii=False, indent=1))
