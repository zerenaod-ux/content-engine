# Content Engine

The 4th system: any topic in, a one-shot animated "living scene" explainer video out (energetic voice, sounds, music). Free tools only, runs on GitHub Actions, no laptop. Nothing is posted.

- Runs by itself twice a day (`.github/workflows/content-engine.yml`, 04:05 and 09:05 UTC). Start by hand: push `publish/run.trigger` (first line `auto` or a topic).
- Each video is saved in its own release (tag `ce-YYYYMMDD-HHMM`); the list is `data/scenes/videos.json`. A `scene-review` issue is opened and shown in the owner's phone app Review tab, plus one ntfy ping.
- `scene_lib/ideas.py` thinks of a new topic and never repeats (`data/scenes/history.json`). `scene_lib/writer.py` plans and writes the scene, `scene_lib/validate.py` checks it, `scene_lib/scene.html` draws it, `scene_lib/assemble.py` adds voice, sound and music.
- Secrets (names only): GROQ_API_KEY, GEMINI_API_KEY (optional: OPENROUTER_API_KEY, CEREBRAS_API_KEY, MISTRAL_API_KEY), NTFY_TOPIC.
- Moved from zerenaod-ux/shelfmade-dashboard on 2026-11-13 so it has its own free writer allowance. Full handover guide: the private notes repo, START-HERE.md.
