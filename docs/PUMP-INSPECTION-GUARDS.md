# Pump narration inspection guards — November 18

The delivered CPU-voice proof remains available for owner review with its inspection warnings. It was not regenerated or approved by this change.

The active daily planner now rejects vertical piston travel for its horizontal pump and steady/continuous discharge claims for the depicted single-acting pump without an accumulator. Registry facts state the actual axis and pulsating discharge explicitly. Regression tests reproduce both statements found in the rendered short and accept the corrected physical descriptions. All 36 local studio checks pass. These guards cover observed contradictions, not universal semantic correctness or creative quality. New cloud verification is required; no new video was started.

Separate monitoring finding: ShelfMade story-short run 44340929933 failed while building two queued stories with HTTP 503 Service Unavailable, producing zero videos. MindLore story-short succeeded. The failing external request and durable queue recovery still require investigation; do not blindly rerun and duplicate generated story drafts.

Cloud verification run 44349043093 passed with the new pump guards. The existing short remains open for owner inspection with warnings; no corrected rerender was requested by this documentation update.

ShelfMade follow-up: the story wrapper prints only the last 900 characters of each worker failure, obscuring the originating request; the retained traceback confirms HTTP 503 but not the specific endpoint. It also counts every failure toward parking a script and persists state only in the later success/release step. A safe recovery needs better retained diagnostics and transient-aware queue persistence before replay. No blind rerun was initiated and no story or owner decision was altered.
