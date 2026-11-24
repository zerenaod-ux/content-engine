# Adding a hand-built machine

1. `python3 tools/new_machine.py my_machine "My machine"` writes `studio_lib/my_machine.py` (a working starter built from `studio_lib/parts_rich.py`) and `machines/_drafts/my_machine.json`.
2. Draw the real machine in the module. `state(t, tl)` returns the numbers the motion checks read; `draw(s, t, tl, hidden=())` must skip any part named in `hidden`.
3. Fill every TODO in the spec, then move it to `machines/my_machine.json`. That one file installs: registry facts, causal motion contract, narration rules, speech-cue anchors, novelty family, topic detection and limits, caption label and motion bounds. No other file is edited.
4. `python3 -m pytest tests/studio/test_machine_specs.py tests/studio/test_picture_check.py` must pass. The picture check also runs before every render and refuses plain, tiny or motionless pictures.

Rich parts: gear (real teeth, recessed web, holes, hub), spring, hook_link, plate, chamfer_box, tube, hex_prism, piston_cylinder, rivets, disc, annulus. Keep decals small and use `bias` on `Scene.face` when a decal must sit in front of a larger face.
