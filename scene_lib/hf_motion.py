"""REAL_MOTION (owner 2026-11-14: the key must really turn, the gears must really spin): one AI picture -> a short AI video
with real movement, made by the free Wan 2.2 image-to-video model on a Hugging Face Space (free ZeroGPU time with the owner's
HF_TOKEN; only a few minutes a day, so only the 1-2 most important shots of each video use it). Returns an mp4 path or None."""
import os, shutil, time

SPACES = ['zerogpu-aoti/wan2-2-fp8da-aoti', 'zerogpu-aoti/wan2-2-fp8da-aoti-faster', 'r3gm/wan2-2-fp8da-aoti-preview2']
NEG = 'melting, warping, deformed, blurry, low quality, text, watermark, morphing, distorted gears'


def animate(image_path, move, out, log=print, seconds=3.5):
    tok = os.environ.get('HF_TOKEN', '').strip()
    if not tok: log('real motion skipped: no HF_TOKEN'); return None
    try: from gradio_client import Client, handle_file
    except Exception as e: log('real motion skipped: gradio_client missing (%s)' % e); return None
    prompt = move + '. Smooth, realistic, physically correct mechanical motion, rigid metal parts keep their shape, steady camera, cinematic macro.'
    for sp in SPACES:
        t0 = time.time()
        try:
            c = Client(sp, hf_token=tok, verbose=False)
            res = c.predict(handle_file(image_path), prompt, NEG, seconds, 1, 1, 6, 42, False, api_name='/generate_video')
            vid = res[0] if isinstance(res, (list, tuple)) else res
            if isinstance(vid, dict): vid = vid.get('video') or vid.get('path')
            if vid and os.path.exists(vid) and os.path.getsize(vid) > 20000:
                shutil.copyfile(vid, out); log('real motion from %s in %.0f s: %s' % (sp, time.time() - t0, move[:70])); return out
            log('real motion: %s gave no video (%s)' % (sp, str(res)[:120]))
        except Exception as e:
            log('real motion: %s failed (%s)' % (sp, str(e)[:160]))
    return None
