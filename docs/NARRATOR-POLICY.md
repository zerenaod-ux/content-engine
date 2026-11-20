# Current narrator: owner-selected clean Heart

The owner chose the corrected Heart sample on November 19. The fixed speaker is now `af_heart` under `how-it-ticks-narrator-v4-heart-clean`. All future short, cinematic and full-format speech routes share this identity, with no provider fallback to another speaker. Shared mastering applies `highpass=f=40` before loudness/headroom processing, matching the correction demonstrated in the selected sample. Mixing contains speech only. Existing media is not recreated. Tests verify offset removal and cache identity; subjective preference comes from the owner's sample selection, not an automated human-naturalness score.

Historical policy and earlier verification follows; the current selection above takes precedence.

# One consistent How It Ticks narrator

November 19, 2026. Owner requested a more attractive voice and the same speaker for every future video.

The stock narrator is now Kokoro `am_fenrir`, fixed under policy `how-it-ticks-narrator-v2`. Daily shorts, cinematic shorts and original full videos share the same narration route. No provider-dependent switch to Andrew or Michael is allowed. If the fixed voice fails, recovery must retry that identity or hold visibly. Old route files cannot select a different speaker, and cached timelines/audio must match the current voice and policy.

Delivery varies by story role: curious opening, slower focused reveal, a quicker emphasized result and a clear upbeat ending. Pace and pauses vary while speaker identity stays fixed. This is stock speech synthesis with pacing controls, not a promise of human acting or unrestricted emotion. Measured duration and encoded loudness gates still apply. Independent measured word timestamps remain mandatory for scene/caption timing.

No existing video is changed or regenerated. A separate four-line audio-only engineering fixture verifies the voice can synthesize, decode and use one identity across delivery roles; it creates no topic, MP4, review card, approval or publication. Listening preference still needs owner judgment.

Voice availability reference: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md

## Verification

Shared cloud verification [44603295259](https://github.com/zerenaod-ux/content-engine/actions/runs/44603295259) passed 190 tests: 23 full-format, 55 cinematic, 32 recovery, 80 daily/component. Identity, stale-cache rejection, same-speaker recovery, measured word timing and absence of a different-speaker fallback are covered.

The first audio fixture generated the fixed voice but lacked the finishing executable. The fixture now provisions that executable explicitly. Voice-only proof [44603568366](https://github.com/zerenaod-ux/content-engine/actions/runs/44603568366) succeeded and produced a 15.50-second preview, with `am_fenrir` used for all four roles. The downloaded preview fully decodes. No video/topic, Studio card, approval or publication was created. Direct human listening and owner preference are not claimed verified.

## Prepared clean-delivery revision

`how-it-ticks-narrator-v3-clean` preserves am_fenrir, lowers delivery rates to +2–6%, and removes the generated tone/effects from final speech mixes. Existing v2 media is retained. This branch revision needs cloud verification and owner listening; tests cannot establish a human-sounding preference.
