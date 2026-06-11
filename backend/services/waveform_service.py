import numpy as np
import soundfile as sf
from pathlib import Path
from typing import List


def generate_waveform_peaks(audio_path: str, samples_per_peak: int = 1000) -> List[List[float]]:
    """Generate min/max peak pairs for waveform visualization.
    Returns list of [min, max] pairs normalized to [-1, 1]."""
    data, sr = sf.read(audio_path, dtype="float32")

    if len(data.shape) > 1:
        data = data.mean(axis=1)

    num_peaks = len(data) // samples_per_peak
    peaks = []

    for i in range(num_peaks):
        chunk = data[i * samples_per_peak: (i + 1) * samples_per_peak]
        peaks.append([float(chunk.min()), float(chunk.max())])

    return peaks


def get_waveform_metadata(audio_path: str) -> dict:
    """Get basic audio metadata for frontend."""
    info = sf.info(audio_path)
    return {
        "duration": info.duration,
        "sample_rate": info.samplerate,
        "channels": info.channels,
    }
