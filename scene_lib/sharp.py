"""SHARP_PICTURES (owner 2026-11-16, measured): the free picture service returns 576x1024 although 1080x1920 is asked, and stretching that ~3x was the blur
in every video. upscale() doubles a picture to real 1152x2048 with the free Real-ESRGAN x2 model on the normal build machine (CPU, no GPU quota).
If the model cannot load it falls back to a clean Lanczos resize + light sharpen and says so."""
import os, time, urllib.request
from pathlib import Path
import cv2, numpy as np
URL = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth'
_M = []

def _model():
    if _M: return _M[0]
    try:
        import torch
        from spandrel import ModelLoader
        p = Path(os.environ.get('CE_CACHE', '/tmp')) / 'RealESRGAN_x2plus.pth'
        if not p.exists() or p.stat().st_size < 1e7: urllib.request.urlretrieve(URL, p)
        m = ModelLoader().load_from_file(str(p)); m.cpu().eval(); torch.set_grad_enabled(False); _M.append(m)
    except Exception as e:
        print('upscaler unavailable (%s): plain resize' % str(e)[:120], flush=True); _M.append(None)
    return _M[0]

def sharpness(img): return float(cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())

def upscale(path, log=print):
    """Doubles the picture in place (only when it is smaller than 1000 px wide). Returns (width, height)."""
    im = cv2.imread(path)
    if im is None: return 0, 0
    h, w = im.shape[:2]
    if w >= 1000: return w, h
    t = time.time(); m = _model(); out = None
    if m is not None:
        try:
            import torch
            x = torch.from_numpy(cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) / 255).permute(2, 0, 1)[None]
            pad_h, pad_w = (-h) % 4, (-w) % 4
            if pad_h or pad_w: x = torch.nn.functional.pad(x, (0, pad_w, 0, pad_h), mode='reflect')
            y = m(x)[0].clamp(0, 1).permute(1, 2, 0).numpy()[:h * 2, :w * 2]
            out = cv2.cvtColor((y * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR)
        except Exception as e: log('upscale failed (%s): plain resize' % str(e)[:100])
    if out is None:
        out = cv2.resize(im, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)
        out = cv2.addWeighted(out, 1.5, cv2.GaussianBlur(out, (0, 0), 2.0), -0.5, 0)
    cv2.imwrite(path, out, [cv2.IMWRITE_JPEG_QUALITY, 95])
    log('upscaled %s: %dx%d -> %dx%d in %.0f s (%s)' % (path, w, h, out.shape[1], out.shape[0], time.time() - t, 'AI model' if m is not None else 'plain resize'))
    return out.shape[1], out.shape[0]
