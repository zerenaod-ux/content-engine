"""MOTION_3D (toned down 2026-11-14: strong depth bending made metal parts look melted) (owner 2026-11-14: pictures must move, not slide): turns one still picture into a moving 3D clip, free, on the CPU.
A free depth model (Depth Anything V2 Small, Apache-2.0, from Hugging Face) guesses how far every pixel is; then the camera
pushes in and drifts sideways so near parts move more than far parts (parallax), like a real camera flying into the object.
python3 scene_lib/parallax.py in.jpg out.mp4 seconds [style]   style: push (default), orbit, rise"""
import subprocess, sys
import numpy as np
import cv2

W, H, FPS = 1080, 1920, 30
_PIPE = []


def depth_map(img_bgr):
    """0 = far, 1 = near. Falls back to a simple centre-weighted guess if the model cannot load."""
    try:
        if not _PIPE:
            from transformers import pipeline
            _PIPE.append(pipeline('depth-estimation', model='depth-anything/Depth-Anything-V2-Small-hf', device=-1))
        from PIL import Image
        d = np.array(_PIPE[0](Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)))['depth'], dtype=np.float32)
        d = cv2.resize(d, (img_bgr.shape[1], img_bgr.shape[0]))
    except Exception as e:
        print('depth model unavailable (%s): simple depth guess' % str(e)[:80], flush=True)
        yy, xx = np.mgrid[0:img_bgr.shape[0], 0:img_bgr.shape[1]].astype(np.float32)
        d = 1 - np.hypot((xx / img_bgr.shape[1] - 0.5), (yy / img_bgr.shape[0] - 0.55)) * 1.6
    d = cv2.GaussianBlur(d, (0, 0), 6)
    lo, hi = np.percentile(d, 2), np.percentile(d, 98)
    return np.clip((d - lo) / max(hi - lo, 1e-6), 0, 1)


def cover(img):
    h, w = img.shape[:2]; s = max(W / w, H / h) * 1.12   # a little extra so edges never show
    img = cv2.resize(img, (int(w * s + 0.5), int(h * s + 0.5)), interpolation=cv2.INTER_CUBIC)
    y0, x0 = (img.shape[0] - int(H * 1.12)) // 2, (img.shape[1] - int(W * 1.12)) // 2
    return img[max(0, y0):max(0, y0) + int(H * 1.12), max(0, x0):max(0, x0) + int(W * 1.12)]


def make_clip(src, out, seconds, style='push'):
    img = cover(cv2.imread(src))
    dep = depth_map(img)
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = w / 2, h / 2
    n = max(2, int(seconds * FPS))
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    dsmall = cv2.resize(dep, (W, H))
    for k in range(n):
        t = k / (n - 1); e = t * t * (3 - 2 * t)        # smooth start and stop
        zoom = 1 + 0.30 * e                              # overall push-in
        near = 0.06 * e                                  # extra push for near parts (the 3D feel)
        sx = {'push': 0.0, 'orbit': 18.0, 'rise': 0.0}[style] * (e - 0.5)
        sy = {'push': 0.0, 'orbit': 0.0, 'rise': -14.0}[style] * (e - 0.5)
        z = zoom * (1 + near * dsmall)
        mx = cx + (xx - W / 2) / z - sx * dsmall
        my = cy + (yy - H / 2) / z - sy * dsmall
        frame = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close(); ff.wait()
    if ff.returncode: raise RuntimeError('parallax encode failed')
    return out


if __name__ == '__main__':
    make_clip(sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else 'push')
