# Full-video repair status

The previous full-video runs stopped when total narration was outside 430–650 words even though every chapter was individually valid. The targeted repair selected only individually invalid chapters, so aggregate-only failures returned the unchanged draft on every attempt. This was a real repair-loop defect, not proof of model incapacity.

The repair now selects up to four shortest chapters for expansion, or longest chapters for shortening, while preserving other chapters, action order, subject and metadata. AI writes the replacements. A regression test covers both aggregate-only underlength and overlength plans. Eighteen full-format tests pass. Final measured 120–300 second and native landscape gates remain unchanged.

Cloud proof is being submitted. Rendering, semantic visual/audio inspection and Studio delivery remain required. No original full-video quality success is claimed yet. Unfinished priority: complete this proof, fix any demonstrated failure, update this status and the handover; review UI work is no longer a reason to drop it.
