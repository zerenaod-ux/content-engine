"""SECOND_GPU (owner 2026-11-14: do not be limited by one free GPU): sends the pictures that Hugging Face could not animate to the
free Kaggle GPU (about 30 h a week, secret KAGGLE_API_TOKEN + KAGGLE_USERNAME) in ONE batch, waits, and returns {out_name: path}.
Same upload/push/wait/download pattern as the AnimationDoodles channel (doodles_engine/kaggle_make.py)."""
import json, os, shutil, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
KERNEL = 'content-engine-motion'


def _kg(*a):
    code = 'import sys;from kaggle.cli import main;sys.argv=["kaggle"]+sys.argv[1:];main()'
    r = subprocess.run([sys.executable, '-c', code, *a], capture_output=True, text=True, env=dict(os.environ))
    return (r.stdout + r.stderr).strip()


def animate_batch(jobs, log=print, max_wait=75 * 60):
    _log = log; log = lambda *a: _log(' '.join(str(x) for x in a))   # the caller's log takes one text
    """jobs: [{"img": path, "move": text, "out": "real03.mp4"}]. Returns {out: local path} for the clips that came back."""
    user = os.environ.get('KAGGLE_USERNAME', '').strip()
    if not jobs: return {}
    if not (os.environ.get('KAGGLE_API_TOKEN') and user): log('Kaggle GPU skipped: KAGGLE_API_TOKEN / KAGGLE_USERNAME not set'); return {}
    ins = Path('kg_in'); shutil.rmtree(ins, ignore_errors=True); ins.mkdir()
    lst = []
    for j in jobs:
        shutil.copy(j['img'], ins / Path(j['img']).name); lst.append({'img': Path(j['img']).name, 'move': j['move'], 'out': j['out']})
    (ins / 'jobs.json').write_text(json.dumps(lst))
    slug = 'ce-motion-' + time.strftime('%d%H%M%S')
    (ins / 'dataset-metadata.json').write_text(json.dumps({'title': slug.replace('-', ' '), 'id': f'{user}/{slug}', 'licenses': [{'name': 'CC0-1.0'}]}))
    for attempt in range(4):
        r = _kg('datasets', 'create', '-p', str(ins)); log('Kaggle upload:', r[-120:])
        if 'error' not in r.lower() and 'problem' not in r.lower(): break
        time.sleep(45)
    else: log('Kaggle upload kept failing'); return {}
    for _ in range(60):
        if 'ready' in _kg('datasets', 'status', f'{user}/{slug}').lower(): break
        time.sleep(10)
    kd = Path('kg_kernel'); shutil.rmtree(kd, ignore_errors=True); kd.mkdir(); shutil.copy(HERE / 'kaggle_motion_kernel.py', kd / 'kaggle_motion_kernel.py')
    (kd / 'kernel-metadata.json').write_text(json.dumps({'id': f'{user}/{KERNEL}', 'title': 'content engine motion', 'code_file': 'kaggle_motion_kernel.py', 'language': 'python',
        'kernel_type': 'script', 'is_private': True, 'enable_gpu': True, 'enable_internet': True, 'dataset_sources': [f'{user}/{slug}'],
        'competition_sources': [], 'kernel_sources': [], 'model_sources': []}))
    r = _kg('kernels', 'push', '-p', str(kd)); log('Kaggle GPU started:', r[-160:])
    t0 = time.time()
    while time.time() - t0 < max_wait:
        time.sleep(45); s = _kg('kernels', 'status', f'{user}/{KERNEL}').lower()
        if 'complete' in s: break
        if 'error' in s or 'cancel' in s: log('Kaggle GPU run failed:', s[-120:]); break
    else: log('Kaggle GPU took too long; using what is ready')
    dl = Path('kg_out'); shutil.rmtree(dl, ignore_errors=True); dl.mkdir(); _kg('kernels', 'output', f'{user}/{KERNEL}', '-p', str(dl))
    for f in dl.rglob('motion.log'): log('Kaggle log:', f.read_text()[-800:])
    got = {}
    for j in jobs:
        f = next(iter(dl.rglob(j['out'])), None)
        if f and f.stat().st_size > 20000: got[j['out']] = str(f)
    log('Kaggle GPU made %d of %d moving clips in %.0f min' % (len(got), len(jobs), (time.time() - t0) / 60))
    return got
