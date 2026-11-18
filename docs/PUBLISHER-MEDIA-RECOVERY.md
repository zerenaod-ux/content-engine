# Approved-media handoff — November 18

The owner approved check-valve short card 55, and filing succeeded. Publisher run 44362291376 booked TikTok but YouTube and Instagram explicitly rejected the CDN media URL. The verified GitHub Pages copy returns HTTP 200, video/mp4, byte-range support and a 12 MB payload.

The publisher now uses the same owned Pages media as an alternative only after an explicit no-post-created media rejection. It verifies the alternative media content type before retrying. Ambiguous transport failures and successful creations are never retried; existing per-platform bookings remain deduplicated by saved state. Exhausted platform failures now fail the job visibly; the existing always-run state-save step retains successful bookings first.

Three local mocked regression tests pass; dedicated cloud verification is pending. No publishing replay was started by the code commit. TikTok must not be rebooked. The approved video's inspection warnings remain recorded; no owner decision was changed.
