import unittest
from unittest.mock import patch
from types import SimpleNamespace
from studio_lib.duration import require_duration, require_video_duration


class DurationTests(unittest.TestCase):
    def test_owner_range_is_inclusive_and_rejects_bad_measurements(self):
        for value in (40, 55.5, 70):
            self.assertEqual(require_duration(value), value)
        for value in (39.99, 70.01, float('nan'), float('inf'), 0):
            with self.assertRaises(ValueError):
                require_duration(value)

    def test_final_media_is_probed_instead_of_trusting_the_plan(self):
        with patch('studio_lib.duration.subprocess.run', return_value=SimpleNamespace(stdout='39.2\n')) as probe:
            with self.assertRaises(ValueError):
                require_video_duration('finished.mp4')
        self.assertIn('ffprobe', probe.call_args.args[0])
