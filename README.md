# Content Engine

The 4th system: any topic in, a one-shot animated "living scene" explainer video out (energetic voice, sounds, music). Free tools only, runs on GitHub Actions, no laptop. Nothing is posted.

- Runs by itself twice a day (`.github/workflows/content-engine.yml`, 04:05 and 09:05 UTC). Start by hand: push `publish/run.trigger` (first line `auto` or a topic).
- Each video is saved in its own release (tag `ce-YYYYMMDD-HHMM`); the list is `data/scenes/videos.json`. A `scene-review` issue is opened and shown in the owner's phone app Review tab, plus one ntfy ping.
- `scene_lib/ideas.py` thinks of a new topic and never repeats (`data/scenes/history.json`). `scene_lib/writer.py` plans and writes the scene, `scene_lib/validate.py` checks it, `scene_lib/scene.html` draws it, `scene_lib/assemble.py` adds voice, sound and music.
- Secrets (names only): GROQ_API_KEY, GEMINI_API_KEY (optional: OPENROUTER_API_KEY, CEREBRAS_API_KEY, MISTRAL_API_KEY), NTFY_TOPIC.
- Moved from zerenaod-ux/shelfmade-dashboard on 2026-11-13 so it has its own free writer allowance. Full handover guide: the private notes repo, START-HERE.md.

## TO CONNECT IT TO YOUTUBE, TIKTOK AND INSTAGRAM (owner steps, in order)
Nothing posts until all 5 steps are done AND the owner says "turn on posting". Do them on a phone or computer, signed out of the other channels' accounts.
1. **New Gmail for this channel**: https://accounts.google.com/signup . Write the address and password in your own password manager (never in GitHub or chat).
2. **YouTube channel** (signed in with the new Gmail): https://www.youtube.com/create_channel . Then https://www.youtube.com/verify (phone verify, needed to upload videos longer than 15 min and custom thumbnails).
3. **TikTok account**: https://www.tiktok.com/signup (choose "Use phone or email" > email > the new Gmail). **Instagram account**: https://www.instagram.com/accounts/emailsignup/ with the new Gmail, then in the app: Settings > Account type and tools > Switch to professional account > Creator.
4. **Free Buffer account** with the new Gmail: https://buffer.com/signup . Then https://publish.buffer.com/channels/connect : connect the TikTok and the Instagram account. In Buffer go to https://publish.buffer.com/settings/api and create an access token; add it in GitHub as the secret `BUFFER_TOKEN` here: https://github.com/zerenaod-ux/content-engine/settings/secrets/actions/new
5. **YouTube permission (one sign-in)**: tell the AI "step 5". It prepares the sign-in link; you open it, sign in with the new Gmail, tap Allow. The AI stores the result as a GitHub secret. Nothing else is needed from you.

What already exists in the other repo and gets copied here after step 5: review cards (Approve/Skip in the phone app), autopilot (checks OK -> approved by itself), the Buffer publisher, the YouTube uploader, phone alerts. Owner advice 2026-11-13: watch one week of videos before turning posting on.

## Picture rules
See PICTURE-RULES.md (owner feedback: pictures must look like the real thing).

## 2026-11-13 — implementation progress (append-only handover)

Evidence inspected: current Content Engine source and workflow at `da2c1f998f81152c17d6844d9dd06477907e16ff`, generation, rendering and review-card path. The preceding review of release `ce-20261113-2105` and its scene JSON/frames found a technically valid video with a narration/visual mismatch: narration promised separated colours while the drawing largely showed a single white line. Its explanation incorrectly suggested beams curl into the rainbow arch; observer geometry and multiple droplets matter. This is not an accurate example to publish. No audio listening or audience testing has been performed.

Edits currently written on the implementation branch (not yet validated as a complete pipeline): variable beat timings within the intended 45–65 seconds; natural narration without compulsory questions/exclamations; per-beat demonstration descriptions and numeric part-change contracts; sampled actual/part-removed rendered visibility checks with explicit limits; accepted plan/scene caching; per-line narration caching; bounded free-service request accounting; preserved last rejected stage/errors; failed ideas no longer permanently ban a subject. Blind post-plan narration rewriting has been removed because it could invalidate the demonstration mapping. Python compilation passed; regression tests and sample verification are still pending.

Remaining work and expected evidence: test claim-to-demonstration mapping and schema failures, timing, cache invalidation/reuse, free-call limits and failure memory; consolidate documentation and creative constraints; render a revised rainbow and substantially different topics. Distinguish deterministic hand-authored fixtures, fresh AI output, actual video renders and human judgment. Numeric/visibility checks cannot establish scientific correctness or viewer understanding. Measure calls and elapsed time per accepted result where live credentials permit; report missing evidence plainly.

Deployment: implementation and samples are in progress. No merge or production rollout. Content Engine posting remains OFF; ShelfMade, MindLore and AnimationDoodles are unchanged. Free quotas are finite; unlimited output and perfect quality are not guaranteed. Preserve existing README text and append further dated measured outcomes instead of replacing this entry.
