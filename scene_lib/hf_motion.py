"""REAL_MOTION (owner 2026-11-14: the key must really turn, the gears must really spin): one AI picture -> a short AI video
with real movement, made by the free Wan 2.2 image-to-video model on a Hugging Face Space (free ZeroGPU time with the owner's
HF_TOKEN; only a few minutes a day, so only the 1-2 most important shots of each video use it). Returns an mp4 path or None."""
import os, shutil, time

SPACES = ['zerogpu-aoti/wan2-2-fp8da-aoti-faster', 'r3gm/wan2-2-fp8da-aoti-preview2', 'zerogpu-aoti/wan2-2-fp8da-aoti', 'Lightricks/ltx-video-distilled', 'Wan-AI/Wan-2.2-5B']
NEG = 'melting, warping, deformed, blurry, low quality, text, watermark, morphing, distorted gears'


QUOTA_GONE = []


def animate(image_path, move, out, log=print, seconds=3.5):
    if QUOTA_GONE: return None   # free daily GPU time already used up: do not ask again today
    tok = os.environ.get('HF_TOKEN', '').strip()
    if not tok: log('real motion skipped: no HF_TOKEN'); return None
    try: from gradio_client import Client, handle_file
    except Exception as e: log('real motion skipped: gradio_client missing (%s)' % e); return None
    prompt = move + '. Smooth, realistic, physically correct mechanical motion, rigid metal parts keep their shape, steady camera, cinematic macro.'
    for sp in SPACES:
        t0 = time.time()
        try:
            try: c = Client(sp, token=tok, verbose=False)        # newer gradio_client
            except TypeError: c = Client(sp, hf_token=tok, verbose=False)
            # ASK_THE_SPACE: read the Space's own list of inputs and fill them by name, so a changed Space does not break us
            api = c.view_api(return_format='dict', print_info=False)
            eps = api.get('named_endpoints', {})
            name = next((n for n in eps if any(w in n for w in ('generate_video', 'image_to_video', 'generate', 'i2v', 'predict'))), None)
            if not name: log('real motion: %s has no video endpoint (%s)' % (sp, list(eps)[:6])); continue
            kw = {}
            for prm in eps[name].get('parameters', []):
                pn = prm.get('parameter_name') or prm.get('label', ''); low = pn.lower()
                if 'neg' in low: kw[pn] = NEG
                elif 'image' in low and 'url' not in low: kw[pn] = handle_file(image_path)
                elif 'prompt' in low: kw[pn] = prompt
                elif 'duration' in low or 'second' in low: kw[pn] = seconds
                elif low in ('mode',) : kw[pn] = 'image-to-video'
            log('real motion: %s %s with %s' % (sp, name, sorted(kw)))
            res = c.predict(api_name=name, **kw)
            vid = res[0] if isinstance(res, (list, tuple)) else res
            if isinstance(vid, dict): vid = vid.get('video') or vid.get('path')
            if vid and os.path.exists(vid) and os.path.getsize(vid) > 20000:
                shutil.copyfile(vid, out); log('real motion from %s in %.0f s: %s' % (sp, time.time() - t0, move[:70])); return out
            log('real motion: %s gave no video (%s)' % (sp, str(res)[:120]))
        except Exception as e:
            log('real motion: %s failed (%s)' % (sp, str(e)[:160]))
            if 'quota' in str(e).lower(): QUOTA_GONE.append(1); log('Hugging Face free GPU time used up for today'); return None
    return None
