# Automatic animation studio experiment

Owner authorized topic-to-video production with no manually repaired generated scenes, using the reviewed drawbridge as a visual reference. This branch adds a separate proof workflow, not a production deployment. Main generation schedule and posting remain unchanged.

The pipeline generates a fresh data-only scene from a topic using configured free model providers, checks bounded schema and rigid parent hierarchies, renders sampled actual/part-removed frames and fixed-camera motion, retries at most three candidates, measures/caches narration, renders a coherent animated scene, and assembles a narrated MP4. No authored topic screenplay or demo fixture is read by generation. The renderer supports general boxes, beams, cylinders, gears, polygons, hierarchies and numeric animation; visual completeness and factual accuracy are not guaranteed by that capability.

The proof matrix covers bridge, solar and piston pump independently, with a fourteen-request/eleven-minute model budget per job and one job at a time to respect free quotas. Outputs, rejected candidates, frames, service ledger, provenance and video hashes are retained as artifacts. Tests use explicitly authored fixtures only for engineering checks. They do not count as automatic-video results. Technical passes never set owner_approved or semantic_verification true.

Current status: eight local behavioral tests pass. Fresh cloud generation and editorial inspection are pending. Do not describe this branch as a proven replacement or re-enable publishing based on tests alone.

## Updated evidence

Two complete batches rejected all six topic trials. Ten local tests pass. The newest quota/critique improvements have not yet completed cloud proof. See STATUS.md for exact evidence, blockers, and the absence of Studio review/progress integration. Production remains unchanged.
