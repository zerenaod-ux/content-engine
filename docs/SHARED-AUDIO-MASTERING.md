# Shared audio mastering

The daily scene encoder now uses studio_lib/audio_mastering.py, also integrated into cinematic short and original full-video test paths. The rule normalizes speech with extra true-peak headroom, a non-amplifying limiter and 48 kHz audio. It does not remove emotional profiles or alter generated text. Cache keys include the helper so old finished audio is not silently reused after this change.

An isolated check of the failed full-video mix measured -16.83 LUFS and -2.91 dB true peak after AAC encoding. A synthetic transient/AAC regression passes. 54 cinematic, 21 full-format, 17 recovery and 34 legacy studio checks pass locally. Two old test-only fixtures were aligned to the existing narration-length policy; production validators were not weakened.

The latest full proof remains pending. Earlier aggregate-length and factual repair failures are recorded, and partial requested repairs are now retained even if the model also outputs an unrequested section. Richer renderer rollout to daily production remains unverified. Auto-approval remains off.
