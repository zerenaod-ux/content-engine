# Daily reservation recovery — November 18

The narration retry for run 44266714493 failed before media generation because the workflow tried to git-rebase its topic-ledger JSON while other cloud jobs updated the same ledger. Repeating git pull inside an unresolved merge could not recover. The Python stage had already exited successfully, leaving a misleading planning stage after the shell failed.

Daily preparation now refreshes the complete remote history and saves reservations through conflict-safe Contents API compare-and-swap. On a conflict it rereads and preserves the other writer's rows; it never resets missing history. Generated index/history changes are merged as local deltas into current remote data instead of rebasing JSON files. The video index is saved before the review card opens. The duplicate checks remain in force.

Explicit recovery requests can resume a failed main scene-factory run only after verifying its source and one original reservation. The original topic and cache are reused; no replacement topic is manually chosen. A new cloud run is needed to use the fixed workflow, rather than blindly retrying an old workflow definition. The old failed run is retained as evidence.

Five regression cases cover concurrent writes, duplicate rejection, idempotent delta persistence, missing-history failure and trusted resumption. Local recovery suite: 22 checks; legacy studio suite: 34 checks. Cloud code verification and resumed-video outcome remain pending. Owner approval stays off; no posting is triggered by this recovery.
