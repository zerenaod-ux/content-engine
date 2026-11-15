# Runs ON the free Kaggle GPU (about 30 h a week). Reads jobs.json from the attached dataset: [{"img": "img03.jpg", "move": "...", "out": "real03.mp4"}].
# Turns each picture into a short real-motion clip with the open LTX-Video image-to-video model, then writes DONE.
import glob, json, os, subprocess, sys, time, traceback
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'   # FIT_T4: first run ran out of the 15 GB GPU memory
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-U', 'diffusers', 'transformers', 'accelerate', 'sentencepiece', 'imageio', 'imageio-ffmpeg'], check=False)
import torch
from diffusers import LTXImageToVideoPipeline
from diffusers.utils import export_to_video, load_image

src = os.path.dirname(glob.glob('/kaggle/input/**/jobs.json', recursive=True)[0])
jobs = json.load(open(os.path.join(src, 'jobs.json')))
OUT = '/kaggle/working'
log = open(os.path.join(OUT, 'motion.log'), 'w')
def say(*a): print(*a, flush=True); log.write(' '.join(map(str, a)) + '\n'); log.flush()
say('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none', 'jobs:', len(jobs))
pipe = LTXImageToVideoPipeline.from_pretrained('Lightricks/LTX-Video', torch_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload()
pipe.vae.enable_tiling()   # decode the video in tiles so it fits in memory
NEG = 'worst quality, static, still image, frozen, no motion, blurry, jittery, distorted, melting, warping, text, watermark'
for j in jobs:
    t0 = time.time()
    try:
        img = load_image(os.path.join(src, j['img'])).resize((480, 704))
        import io; _b = io.BytesIO(); img.save(_b, 'JPEG', quality=35); from PIL import Image as _I; img = _I.open(io.BytesIO(_b.getvalue())).convert('RGB')   # MORE_MOTION: pristine pictures make LTX freeze; compression noise wakes it up
        frames = pipe(image=img, prompt=j['move'] + '. The motion starts right away and is large, fast and clearly visible, like real life. The camera moves with the action. Bright lighting, sharp detail.',
                      negative_prompt=NEG, width=480, height=704, num_frames=49, num_inference_steps=20, guidance_scale=4.0, decode_timestep=0.03, decode_noise_scale=0.025).frames[0]
        export_to_video(frames, os.path.join(OUT, j['out']), fps=24)
        say('ok', j['out'], '%.0f s' % (time.time() - t0))
    except Exception:
        say('fail', j['out'], traceback.format_exc()[-400:])
    torch.cuda.empty_cache()
open(os.path.join(OUT, 'DONE'), 'w').write('ok')
