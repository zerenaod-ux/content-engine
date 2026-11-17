"""Owner's short-video duration policy, based on measured media, not word count."""
import math
import subprocess

MIN_SECONDS = 40.0
MAX_SECONDS = 70.0


def require_duration(seconds):
    value = float(seconds)
    if not math.isfinite(value) or not MIN_SECONDS <= value <= MAX_SECONDS:
        raise ValueError('Short video must be 40-70 seconds; measured %.3f seconds. Repair narration and actions, never pad with silence.' % value)
    return value


def require_video_duration(path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(path)], capture_output=True, text=True, check=True)
    return require_duration(result.stdout.strip())
