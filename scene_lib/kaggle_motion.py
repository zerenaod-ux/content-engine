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


def animate_batch(jobs, log=print, max_wait=120 * 60):
    _log = log; log = lambda *a: _log(' '.join(str(x) for x in a))   # the caller's log takes one text
    """jobs: [{"img": path, "move": text, "out": "real03.mp4"}]. Returns {out: local path} for the clips that came back."""
    user = os.environ.get('KAGGLE_USERNAME', '').strip()
    if not jobs: return {}
    if not (os.environ.get('KAGGLE_API_TOKEN') and user): log('Kaggle GPU skipped: KAGGLE_API_TOKEN / KAGGLE_USERNAME not set'); return {}
    # TWO_GPUS (owner 2026-11-15: use as much free GPU as possible): split the shots over two Kaggle runs at the same time
    parts = [jobs[0::2], jobs[1::2]] if len(jobs) > 3 else [jobs]
    names, pending = [], []   # pending: runs Kaggle refused for now (GPU session limit); retried while the others work
    for n, part in enumerate(parts):
        kern = KERNEL if n == 0 else KERNEL + '-b'
        for _ in range(20):   # BUSY_CHECK: Kaggle allows 2 GPU runs at once; wait (max 15 min) if an older run is still busy
            st = _kg('kernels', 'status', f'{user}/{kern}').lower()
            if 'running' not in st and 'queued' not in st: break
            log('Kaggle GPU %d still busy with an older run; waiting' % n); time.sleep(45)
        ins = Path('kg_in%d' % n); shutil.rmtree(ins, ignore_errors=True); ins.mkdir()
        lst = []
        for j in part:
            shutil.copy(j['img'], ins / Path(j['img']).name); lst.append({'img': Path(j['img']).name, 'move': j['move'], 'out': j['out']})
        (ins / 'jobs.json').write_text(json.dumps(lst))
        slug = 'ce-motion-%d-' % n + time.strftime('%d%H%M%S')
        (ins / 'dataset-metadata.json').write_text(json.dumps({'title': slug.replace('-', ' '), 'id': f'{user}/{slug}', 'licenses': [{'name': 'CC0-1.0'}]}))
        for attempt in range(4):
            r = _kg('datasets', 'create', '-p', str(ins)); log('Kaggle upload %d:' % n, r[-120:])
            if 'error' not in r.lower() and 'problem' not in r.lower(): break
            time.sleep(45)
        else: log('Kaggle upload kept failing'); continue
        for _ in range(60):
            if 'ready' in _kg('datasets', 'status', f'{user}/{slug}').lower(): break
            time.sleep(10)
        kd = Path('kg_kernel%d' % n); shutil.rmtree(kd, ignore_errors=True); kd.mkdir(); shutil.copy(HERE / 'kaggle_motion_kernel.py', kd / 'kaggle_motion_kernel.py')
        (kd / 'kernel-metadata.json').write_text(json.dumps({'id': f'{user}/{kern}', 'title': kern.replace('-', ' '), 'code_file': 'kaggle_motion_kernel.py', 'language': 'python',
            'kernel_type': 'script', 'is_private': True, 'enable_gpu': True, 'enable_internet': True, 'dataset_sources': [f'{user}/{slug}'],
            'competition_sources': [], 'kernel_sources': [], 'model_sources': []}))
        r = _kg('kernels', 'push', '-p', str(kd)); log('Kaggle GPU %d started:' % n, r[-160:])
        if 'error' not in r.lower(): names.append(kern)
        else: pending.append((n, kd, kern))
    t0 = time.time(); left = set(names)
    while (left or pending) and time.time() - t0 < max_wait:
        time.sleep(45)
        for item in list(pending):   # RETRY_PUSH: another job of this account (e.g. a Doodles video) may hold a GPU session; try again every 45 s
            r = _kg('kernels', 'push', '-p', str(item[1]))
            if 'error' not in r.lower(): log('Kaggle GPU %d started later:' % item[0], r[-100:]); names.append(item[2]); left.add(item[2]); pending.remove(item)
        for kern in list(left):
            s = _kg('kernels', 'status', f'{user}/{kern}').lower()
            if 'complete' in s: left.discard(kern)
            elif 'error' in s or 'cancel' in s: log('Kaggle GPU run failed:', kern, s[-120:]); left.discard(kern)
    if left: log('Kaggle GPU took too long; using what is ready')
    dl = Path('kg_out'); shutil.rmtree(dl, ignore_errors=True); dl.mkdir()
    for n, kern in enumerate(names):
        d = dl / str(n); d.mkdir(); _kg('kernels', 'output', f'{user}/{kern}', '-p', str(d))
    for f in dl.rglob('motion.log'): log('Kaggle log:', f.read_text()[-800:])
    got = {}
    for j in jobs:
        f = next(iter(dl.rglob(j['out'])), None)
        if f and f.stat().st_size > 20000: got[j['out']] = str(f)
    log('Kaggle GPU made %d of %d moving clips in %.0f min' % (len(got), len(jobs), (time.time() - t0) / 60))
    return got
