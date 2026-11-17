# How It Ticks — current verified status
Updated November 17, 2026 (America/Chicago). This page supersedes older dated status claims; historical README entries are retained.

## Live system
- The tested-component pipeline is deployed on main. Four supported mechanism families: bascule bridge, photovoltaic cell/panel, single-acting piston water pump, direct-drive wind turbine. Arbitrary-topic animation is not supported.
- Seven new-style shorts and one long compilation were identified in release/review records. The index lists 35 short-video entries across old and new systems; it omits the newest long compilation. These counts are observations, not promises of future totals.
- Daily short generation is scheduled at 3:05 AM Chicago. A separate long-video workflow uses a day-of-month cron intended for alternating days; it joins existing shorts into a branded 16:9 compilation, rather than independently writing a long explanation.
- Automatic approval is OFF, explicitly requested and verified November 17. Existing already-approved videos are not revoked. New decisions require owner review.
- Publishing is ON for approved/Saved items. The latest inspected publisher run scheduled zero items; the inspected state contains no successful YouTube posting record for today. The YouTube channel itself was not directly verified.

## Verified playback and defects
- Latest short: “Why Direct-Drive Turbines Skip Gearboxes Efficiently,” approximately 48 seconds, 720x1280. Its direct video opened and playback advanced without a reported media error. This was sampled playback, not a complete scientific/narration/audio review.
- Latest long: “How Machines Work From the Inside,” approximately 3 minutes 19 seconds, 1920x1080. Its direct Pages link opened and played.
- Long generation run [completed with a hidden index-save failure](https://github.com/zerenaod-ux/content-engine/actions/runs/44008595270): release, phone copy and review card exist, but concurrent history/index changes caused a rebase conflict. The retry shell loop did not propagate that failure, so GitHub incorrectly marked the whole job successful. The long index entry and reuse bookkeeping need reconciliation, and save failures must fail visibly. No repair has been made in this documentation update.
- README opening sections and older histories describe earlier architectures/settings. Consult this page and actual workflow/configuration files for current state.

## Current cinematic upgrade — NOT deployed
The owner requested improvements after inspecting Zack D. Films reference Shorts. Two sampled references were [cup drop](https://www.youtube.com/shorts/quePIIHPDeY) and [Oreo twisting machine](https://www.youtube.com/shorts/QJqqRN6dssk). Visible observations: detailed 3D objects, tight framing, mechanism close-ups, short changing captions. Exact production software, staffing, full sound design and acoustic speaker characteristics were not established.

Implementation is in the draft [automatic cinematic wind-turbine comparison](https://github.com/zerenaod-ux/content-engine/pull/41), branch `studio-cinematic-proof`, source `3c7a1bc342cbf4a6ab5a647068e5a3a33b988053`. The [first cloud comparison](https://github.com/zerenaod-ux/content-engine/actions/runs/44051234755) is in progress at this update. No upgraded video has passed inspection yet.

| Item | Implemented system change | Evidence/status |
|---|---|---|
| 1. Story | Topic-driven original model script, direct opening, concrete actions and causal explanation, bounded validation and factual critique | Code submitted; generated story not yet inspected |
| 2. Visuals | Reusable Blender turbine with thick blades, bearings, brake, magnets, copper windings, tower/environment, studio lighting, shadows and cavity shading | Code submitted; first cloud render pending. Workbench is a fast illustrative renderer, not a photorealism claim |
| 3. Camera | Full-frame overview, rotor/shaft/generator/coil/load views, eased transitions and small push-ins driven by the measured narration timeline | Code submitted; actual framing pending inspection |
| 4. Speech | Original Andrew TTS voice, conversational script instructions, per-beat rate variation, measured durations and short pauses | Code submitted; reference audio was not acoustically matched or voice-cloned; generated delivery pending review |
| 5. Captions and sound | Up to three words per caption using actual synthesis WordBoundary metadata, escaped subtitle control text, ducked music/swishes and a switch click aligned to action | Three local tests pass for grouping, timestamp formatting and text handling; full audiovisual synchronization pending |
| 6. Automatic proof | GitHub generates script, voice, animation, captions, mix and final MP4 from a topic; retains raw scripts, measured timeline, diagnostic frames, Blender scene and provenance | Cloud run active. No manual script/video edits; no finished quality pass yet |

Five items are implemented in code; zero of six are fully verified in the upgraded finished video as of this update. Unit tests are not a visual, factual or audio-quality pass.

## Review checklist when output finishes
Inspect all eight action beats; verify that the spoken part is in view, rotor/shaft/magnets stay coupled, coils remain stationary, the opening is direct, the lamp switch and payoff match narration, and no critical object clips or disappears. Check word-caption timing, readability and safe margins; speech intelligibility, pauses, bed ducking and transient levels; full MP4 decoding and duration. Record measured build time, provider use, observed flaws and final source. If a flaw is found, change system code and rerun; never hand-edit the generated comparison to manufacture a pass.

The comparison workflow has read-only repository permissions and cannot publish, change owner review decisions, or turn approval on. Production renderer, generation schedule, other channels and posting settings are not changed by this experiment. Free cloud quotas remain finite.

## Next actions
1. Finish and inspect the automatic comparison; report each of the six items against actual evidence.
2. Correct any observed defects in the system, rerun boundedly, and preserve rejected outputs.
3. Show the finished comparison before applying the renderer broadly.
4. Separately repair the known long-video index/save failure. This remains outstanding.


## November 17 — Studio review delivery added during the comparison run
The owner clarified that every completed comparison must appear in Studio Review. A separate delivery workflow is now deployed on main: it listens for successful cinematic-comparison runs, validates their source/provenance, preserves the mobile MP4 in gh-pages and a release, merges the current video index with collision retries, and opens an idempotent checks-warn review card only after those saves succeed. It does not approve or publish. Automatic approval remains off. This is delivery integration, not deployment of the new renderer as the daily production default. Five local tests now pass: the three caption tests plus preserving concurrent index entries on retry and rejecting failed/untrusted source runs before writes. Delivery is not yet verified end to end because the first render is still running. No independent wake-up/failure-notification monitor is configured; status is being checked during the active task.


## 2026-11-17 — corrected hand-generator comparison delivered (append-only)

The system generated a fresh topic, “How a hand-cranked generator turns effort into light,” without manual generated-script or video edits. Earlier output 44066025188 passed audio tests but was rejected on inspection for stationary-core/cover narration errors; its Studio card is explicitly marked as needing correction. A subsequent script-only attempt 44068378801 was rejected before rendering. The writer now preserves valid lines during bounded repairs, allows stationary supporting bearings, and rejects offset-shaft, stationary-core torque, cover-direction, lamp-closes-circuit and pre-switch current claims.

Final cloud run 44068968307 completed successfully and produced 38.376 seconds in 579.878 seconds (about 9.7 minutes for the build). Script, encoded-frame samples across the sequence, caption intervals and independent audio transcript were inspected. The corrected explanation describes induced voltage with the switch open, then current through the lamp after closure. Forty-one caption groups have zero overlaps and do not cross beat boundaries. Speech is modestly faster (+26/+32 percent TTS settings, about 183 words/minute overall); coupled rotor/crank motion is about 15 percent faster than the previous cinematic version.

Encoded audio: -16.28 LUFS integrated loudness, -1.23 dB true peak, 2.56 percent independent ASR word error rate; full media decode passed. This is automated audio verification and transcript review, NOT a claim of human listening or subjective aesthetic approval. Eleven local tests pass. The cloud run passed its applicable tests and audio gate.

Delivery run 44070603413 succeeded. Studio card: https://github.com/zerenaod-ux/content-engine/issues/45 . Title: “How Turning a Handle Lights a Lamp 💡”. Its index entry exists and the immutable mobile MP4 returned HTTP 200 with video/mp4 and byte-range support. Original and rejected samples remain separate. Automatic approval is verified OFF. No approval or publishing action was taken. The cinematic renderer remains a tested comparison workflow on its branch, not the daily production default; owner review is still required before a broad rollout. The older long-video index defect remains separate and unresolved.


## November 17 — three daily generation slots and cinematic review fixes

Owner authorized three daily new-topic generation slots. Main scene-factory schedule is now 01:05, 09:05 and 17:05 UTC (3:05 AM, 11:05 AM and 7:05 PM Chicago standard time; one hour later during daylight saving). These are scheduled attempts, not a promise of three completed quality videos despite provider outages or unsupported/exhausted topics. Each finished video still requires manual Approve/Skip; automatic approval remains off. Publisher reads Saved only and retains its existing cadence/settings.

Added a full-history/index topic guard with no expiry, canonical/close-lexical duplicate checks, and durable reservations saved before rendering. Automatic selection can reject up to four repeated candidates. Failure to read history or persist a reservation stops generation. Rephrased meanings beyond these checks are not guaranteed detectable; history is never intentionally truncated. Failed/unavailable topics do not justify substituting a repeated video. The live daily renderer remains the existing tested component pipeline; new cinematic diagram prototypes are not silently deployed as daily defaults.

Found the approved cinematic wind card stuck before Saved because review URL/tag parsing rejected the `-cinema-<run>` suffix. Extended the strict same-repository MP4 allowlist to accept this exact suffix for Approve and Skip. Existing approval labels will be reconciled by the review workflow; no new approval is invented. Older unindexed review cards may still report unrelated errors.

Also registered the six named diagram subjects in cinematic delivery so successful new-component runs can use the established immutable mobile MP4/index/review path. They retain checks-warn and owner review; nothing automatically approves or publishes new samples. First hydraulic artifact rendered with automated audio passing but failed delivery due to the prior two-subject allowlist. Visual inspection found an unrelated circuit-marker caption on the hydraulic payoff; it is not a quality pass and needs a system correction/rerender before being presented as ready.

Validation before save: four topic-guard tests, three cinematic-tag tests, workflow YAML and every shell block syntax passed. No new production video was requested by this configuration commit. Already-approved publishing is authorized by the owner; no posting action or approval switch is changed here.


## November 17 — confirmed output, Studio delivery and publishing read-back

Corrected hydraulic diagram run completed from the topic using its saved accepted model-written script and eight cached voice lines: 38.672 seconds, 288.75 seconds build time, zero new voice requests and no manual generated-script/video edits. Playback decode, caption checks and automated audio checks passed (-16.44 LUFS, -1.3 dB true peak, 0% ASR word error, about 185 words/minute). Sampled encoded frames confirm the unrelated circuit disclosure is removed and label contrast improved. Direct human listening was NOT performed. Owner aesthetic/scientific approval is still required; this is a simplified hydraulic schematic, not a photorealistic device or proof for arbitrary topics.

Studio delivery succeeded. Indexed card: “Why Hydraulic Lifts Trade Travel 🏗️”, issue 46, source run 44136986640. Immutable mobile MP4 saved and review card open; no approval/publishing decision made for the hydraulic sample. Only the corrected sample was delivered; the earlier failed-delivery artifact is retained as evidence.

Recovered the owner's existing approval for “Why Direct-Drive Needs No Gearbox”: review tag parsing now accepts the precise cinematic suffix, the video is in Saved, and its card is closed. Initial publishing queued Instagram/TikTok but YouTube refused to read the video URL. Added a bounded retry only for explicit media-fetch rejection, never retrying ambiguous creation failures/successes; unsuccessful handoffs now fail visibly while retaining successful per-platform state. Retrying scheduled only YouTube. Read-only Buffer verification confirmed one scheduled copy per platform: YouTube November 17 at 12:30 PM Chicago, TikTok at 6 PM, Instagram at 7 PM. These are scheduled, NOT confirmed live publications.

Owner clarified the ongoing target: three new generation attempts daily and two approved videos published daily per platform. Configuration has three creation slots and two per-platform publishing slots. Actual sustained daily output is not yet proven and requires sufficient approved videos/provider capacity. Newest unscheduled approvals now fill future slots first; already scheduled or published records are kept and not duplicated. Automatic approval remains off. The new six diagram prototypes remain in the cinematic test branch; daily production still uses its existing supported-component renderer. There is no guarantee of every possible topic or perfect semantic duplicate detection.

Known separate issues: two legacy review cards have no valid indexed video, so review reconciliation can still report those failures even though the approved wind card was filed correctly. The older long-video indexing defect remains outside this change. No assets or owner decisions were deleted or reset.


## November 17 — operational parity audit

Compared How It Ticks with the other three Studio systems. Existing Buffer views are integrated with explicit report timestamps; direct YouTube subscriber/watch-time OAuth analytics remain a separate integration, not claimed as added. Studio's shared job list now includes How It Ticks production, publishing, filing, status checks and experimental runs, preserving failures and unknown status. Home/Channels retain one shared fourth-system card. Review list pagination is shared with counts rather than silently stopping at 50 or 100 cards. Concurrent identical data reads are coalesced without retaining stale results.

Publisher will also check Saved after the review-folder workflow completes on main, avoiding the previous up-to-three-hour polling delay. Its existing three-hour schedule remains a fallback. It still publishes only existing owner-approved Saved items, with the same two daily slots per platform and no automatic approval. Exhausted state-save retries now fail visibly rather than falsely report success. Mocked save checks covered pull failure, push failure, and successful persistence; no publication was manually initiated for this audit. Existing experimental-video and legacy filing failures are visible and are not resolved merely by this UI change.


## Owner duration rule — November 17

New short videos must measure 40–70 seconds. Generation now targets 140–176 spoken words with meaningful explanation, not silence or loops. Both measured narration and final encoded daily MP4 are checked, and cinematic delivery also requires a compliant duration. Older approved/scheduled videos are not changed. Cinematic branch applies the same measured checks before rendering and after encoding. Local duration boundary/probe tests and the cinematic suite pass; no new successful output is claimed by these tests. Richer internal motion remains separate work.


## November 17 — recovery verification, 4:28 PM Chicago

Review-folder recovery run completed successfully after restoring two missing original-release index entries and adding strict legacy `-pN` and long-video identifiers. Existing owner decisions on the microwave, old drawbridge, solar prototype, bridge prototype and wind prototype cards were preserved; all five cards now close only after folder persistence. No fresh approval was manufactured.

Read-only publishing verification saved a fresh snapshot at 22:27 UTC: one YouTube post confirmed sent, two YouTube scheduled, and three each scheduled on TikTok/Instagram. Buffer views remain an older report and must not be read as current native YouTube analytics.

The previous lever retry accepted a 142-word model-written repair but failed at the free voice service with NoAudioReceived. Updated narration uses bounded request timeouts, discards incomplete cache entries and spaces retries 10/20/40 seconds, retaining completed lines and the accepted script. Forty-five local cinematic checks pass, including empty-response recovery and no new calls on a complete cache. Recovery run is in progress; no new finished output or richer visual quality pass is claimed. A service outage can still exhaust these bounded retries. Direct YouTube analytics and deeper internal mechanism animation remain unfinished. Doodles' existing GPU budget warning currently measures entire workflow elapsed time rather than actual GPU billing; that difference requires correction before claiming measured quota exhaustion.


## November 17 — current production contract and full-video redesign

Owner requires system-selected unique topics, meaningful multi-stage causal motion, shorts of 40–70 seconds, and a separate original 2–5-minute native-widescreen single-topic pipeline. Current ce_long.py concatenates shorts with side panels; two existing full-video releases repeat the same compilation title. This legacy pipeline does NOT meet the new requirement and has not yet been replaced. See [the current production planner](PRODUCTION-PLANNER.md) for acceptance criteria and verified versus unfinished work. Automatic topic proof is running; no new-topic success is claimed yet. The 42.104-second lever recovery reached Studio with passing automated audio but is labeled not a richer-motion quality pass. Earlier entries are retained as historical evidence.


## November 17 — executable original full-video proof

Implemented on studio-cinematic-proof: original system-selected long topic within two explicit mechanism scopes (rack-and-pinion or rotating lead screw), 16 causal narration chapters, direct native 1280×720 procedural rendering, shared expressive measured narration, 120–300-second encoded-media gate, automated audio review, archival/index save and Studio review delivery. No existing short MP4 is loaded or joined. Five full-format tests and 48 shared cinematic tests passed locally and on the first cloud job. The first cloud attempt stopped before selecting a topic because the reservation ledger file had never been initialized on main. Full history and video indexes exist and remain untouched. Initializing only that missing reservation ledger is safe and preserves all recorded topic history. Cloud rerun remains necessary; no finished original full video, inspected quality pass or production replacement is claimed.
