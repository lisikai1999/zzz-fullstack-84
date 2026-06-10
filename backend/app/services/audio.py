import subprocess
import tempfile
from pathlib import Path


def extract_audio_to_wav(input_path: str, output_path: str | None = None) -> str:
    input_p = Path(input_path)
    if output_path is None:
        output_path = str(input_p.with_suffix(".wav"))

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def get_audio_duration(audio_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())
