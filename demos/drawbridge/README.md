# Drawbridge animation-studio prototype

Authorized by the owner on 2026-11-16: rebuild one coherent drawbridge demonstration, measure it, show it before applying the approach system-wide. This is an authored, stylized prototype; it does not demonstrate automatic planning or general video quality. No production workflow, schedule, credentials, review decision or publisher is modified.

## What is reusable

`render.py` provides perspective meshes, rigid transforms, boxes/beams/cylinders/gears, eased camera choreography, a bascule bridge, traffic barriers, car, ship, and a deterministic timeline. The roadway and counterweight use the same rotation around a fixed pivot. Motor pinion rotation opposes the pivot gear at their tooth-count ratio. The chamber cutaway reveals otherwise occluded parts. These are illustrative proportions, not a structural design or simulation. Further scenes can reuse these components; integration into automatic scene planning is not implemented.

`voice.py` caches each line by text and voice parameters, probes actual duration and gives it sufficient time without stretching speech. It preserves the documented Andrew voice at +30% / +8 Hz. The free online service initially returned no audio; subsequent bounded attempts completed. Nothing silently switches to a substitute voice.

`assemble.py` reuses generated sound/music functions, synchronizes motor sound to leaf movement, mixes quiet effects beneath narration, ducks music during speech, and normalizes the final audio. No downloaded or paid sound assets are used.

## Run

From the repository root, with Python containing numpy, Pillow and edge-tts, plus ffmpeg/ffprobe:

```sh
python demos/drawbridge/voice.py
python demos/drawbridge/verify.py
python demos/drawbridge/render.py --preview
python demos/drawbridge/render.py
python demos/drawbridge/assemble.py
```

Render must finish successfully before assembly. Output is local under `output/`, ignored by Git; original videos are preserved. The fonts currently use macOS Arial paths; a cloud adapter must supply portable fonts before deployment.

## Evidence and limits

Output: 53-second portrait, 720×1280, 30fps H.264/AAC. Preview frame sheets, movement/sequence checks and separate voice/render/audio measurements are retained locally. CPU animation makes no image-generation or model calls; new narration still uses an online service. Eight checks cover opening direction, counterweight descent, fixed pivot, barriers closed while raised, ship timing, road return before traffic, voice fit and sampled brightness. These checks do not establish gear engineering, realistic textures, audible quality or viewer appeal. Human approval remains pending.

Physical reference: [NCDOT: Bascule Bridges](https://www.ncdot.gov/initiatives-policies/Transportation/bridges/historic-bridges/bridge-types/Pages/bascule.aspx). It describes seesaw rotation, a fixed trunnion and a heel counterweight. The demo represents one simplified bridge type; it does not suggest all drawbridges have this mechanism.


## 2026-11-16 — owner review corrections

Owner judged the overall bridge opening/closing better, and requested fixes for the road hole, disappearing ship, unclear gear rotation and stronger camera close-ups. The far approach began at x=3.3 while the leaf ended at x=2.8; it now meets exactly at x=2.8, with road surfaces at the same elevation. Road meshes are subdivided to avoid a long painter-sorted face hiding the car. Water is painted as a separate background layer: sorting its huge polygon by average depth had painted over the distant ship. Near-plane polygon clipping keeps the water present during the tighter zoom. The ship is no longer conditionally omitted during a cutaway and continues on a smooth path after passage. Gears retain the physically coupled opposing rotations, now with asymmetric front-face reference marks; the drive beat eases into a closer camera view and back out. The original leaf opening/closing curve is unchanged. All eight original checks plus five targeted regressions pass, including actual ship-versus-ship-removed pixel comparisons through the last shot and visible pinion rotation with a fixed camera. Original MP4 retained as drawbridge-review-v1.mp4; revision uses a distinct v2 filename. This revision reuses all voice assets and makes zero new model, image or narration service calls. Owner approval of the revision remains pending.
