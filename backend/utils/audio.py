import subprocess
import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def extract_audio_to_wav(input_path: Path, output_path: Path) -> Path:
    """Extract audio from video/audio file and convert to 16kHz mono WAV for Whisper."""
    if not ensure_ffmpeg():
        logger.warning("ffmpeg not found, copying file directly")
        if input_path.suffix.lower() in ('.wav', '.wave'):
            shutil.copy2(input_path, output_path)
            return output_path
        raise RuntimeError("ffmpeg is required to convert non-WAV audio files")

    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def get_audio_duration(file_path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    if not shutil.which("ffprobe"):
        try:
            import soundfile as sf
            info = sf.info(str(file_path))
            return info.duration
        except Exception:
            return 0.0
    cmd = [
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(file_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def ensure_ffmpeg():
    """Check if ffmpeg is available."""
    return shutil.which("ffmpeg") is not None
