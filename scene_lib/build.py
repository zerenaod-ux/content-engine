"""Reuse a checked finished result; otherwise render/check/assemble once.
Cache metadata verifies the result bytes; changes to inputs or implementation
invalidate it. No cache entry is written when any build stage fails.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scene_lib.validate import check


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def result_key(spec):
    h = hashlib.sha256(json.dumps(spec, sort_keys=True).encode())
    for p in ['scene_lib/render.js','scene_lib/scene.html','scene_lib/check_frames.py',
              'scene_lib/evidence.py','scene_lib/validate.py','scene_lib/catalog.py',
              'scene_lib/assemble.py','scene_lib/audio.py','local_voice.py','scene_lib/build.py',
              'scene_lib/prepare.py','scene_lib/repair.py','scene_lib/writer.py']:
        h.update((ROOT/p).read_bytes())
    h.update(os.environ.get('SCENE_VOICE','default').encode())
    # Dependency versions affect rendering/audio; cache is platform-specific too.
    import platform, importlib.metadata
    h.update(platform.platform().encode())
    for package in ('numpy','pillow','edge-tts','imageio-ffmpeg'):
        try: h.update((package+importlib.metadata.version(package)).encode())
        except importlib.metadata.PackageNotFoundError: h.update((package+':missing').encode())
    package_path=ROOT/'node_modules/playwright/package.json'
    if package_path.exists(): h.update(package_path.read_bytes())
    return h.hexdigest()


def main(spec_path, out):
    started = time.monotonic()
    spec = json.loads(Path(spec_path).read_text())
    errors = check(spec)
    if errors: raise ValueError('scene rejected: ' + ' | '.join(errors[:8]))
    cache = Path(os.environ.get('CE_CACHE_DIR','.ce-cache')) / 'results' / result_key(spec)
    hit = False
    try:
        meta = json.loads((cache/'metadata.json').read_text())
        hit = all(digest(cache/name) == expected for name,expected in meta.items()) and set(meta) == {'video.mp4','evidence-report.json','scene.json'}
    except (OSError, ValueError, TypeError, AttributeError): pass
    if hit:
        shutil.copyfile(cache/'video.mp4',out)
        shutil.copyfile(cache/'scene.json',spec_path)
        shutil.copyfile(cache/'evidence-report.json','evidence-report.json')
        print('result cache hit: no rendering or narration calls')
    else:
        from scene_lib.repair import repair
        for attempt in range(2):
            # New run directory keeps the previous render for inspection.
            if Path('fr').exists():
                old = Path('attempts') / ('frames-%d-%d' % (int(time.time()), attempt))
                old.parent.mkdir(exist_ok=True); shutil.move('fr',old)
            subprocess.run(['node',str(ROOT/'scene_lib/render.js'),spec_path],check=True)
            result=subprocess.run([sys.executable,str(ROOT/'scene_lib/check_frames.py'),spec_path])
            current=json.loads(Path(spec_path).read_text())
            errors=check(current)
            if result.returncode == 0 and not errors: break
            report=json.loads(Path('evidence-report.json').read_text())
            report['errors'] += errors
            Path('attempts').mkdir(exist_ok=True)
            Path('attempts/render-rejected.json').write_text(json.dumps({'scene':current,'report':report},indent=1))
            if attempt: raise ValueError('render repair still rejected; all evidence retained')
            context_path=os.environ.get('CE_REPAIR_CONTEXT')
            context=Path(context_path).read_text() if context_path else ''
            fixed=repair(current,report['errors'],context)
            Path(spec_path).write_text(json.dumps(fixed,indent=1,ensure_ascii=False))
        subprocess.run([sys.executable,str(ROOT/'scene_lib/assemble.py'),spec_path,out],check=True)
        cache.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(out,cache/'video.mp4')
        shutil.copyfile(spec_path,cache/'scene.json')
        shutil.copyfile('evidence-report.json',cache/'evidence-report.json')
        (cache/'metadata.json').write_text(json.dumps({n:digest(cache/n) for n in ['video.mp4','evidence-report.json','scene.json']}))
    p=Path(os.environ.get('CE_METRICS_PATH','metrics.json'))
    try: metrics=json.loads(p.read_text())
    except (OSError,ValueError): metrics={'requests':0,'responses':0,'failures':0,'seconds':0}
    metrics.update(accepted_build_seconds=round(time.monotonic()-started,3),result_cache_hit=hit,
                   automatic_checks_passed=True,semantic_verification=False)
    p.write_text(json.dumps(metrics,indent=1))


if __name__ == '__main__': main(sys.argv[1],sys.argv[2])
