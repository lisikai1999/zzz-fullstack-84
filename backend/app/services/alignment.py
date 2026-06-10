import json
import tempfile
import wave
import struct
from pathlib import Path

import numpy as np
from scipy.signal import medfilt
import jieba

from app.services.audio import extract_audio_to_wav, get_audio_duration

try:
    from aeneas.executetask import ExecuteTask
    from aeneas.task import Task as AeneasTask
    HAS_AENEAS = True
except ImportError:
    HAS_AENEAS = False

HOP_MS = 10
FRAME_MS = 25


def align_transcript(audio_path: str, transcript_path: str, progress_callback=None) -> list[dict]:
    transcript_text = Path(transcript_path).read_text(encoding="utf-8").strip()
    words = list(jieba.cut(transcript_text))
    words = [w.strip() for w in words if w.strip()]

    if not words:
        return []

    if not HAS_AENEAS:
        return _energy_based_align(words, audio_path, progress_callback)

    wav_path = audio_path
    if not audio_path.endswith(".wav"):
        wav_path = extract_audio_to_wav(audio_path)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for word in words:
            f.write(word + "\n")
        text_file = f.name

    output_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name

    config_string = "|".join([
        "task_language=cmn",
        "is_text_type=plain",
        "os_task_file_format=json",
        "task_adjust_boundary_algorithm=auto",
        "task_adjust_boundary_nonspeech_min=0.200",
        "task_adjust_boundary_nonspeech_string=SIL",
    ])

    task = AeneasTask(config_string=config_string)
    task.audio_file_path_absolute = wav_path
    task.text_file_path_absolute = text_file
    task.sync_map_file_path_absolute = output_file

    executor = ExecuteTask(task=task)
    executor.execute()
    task.output_sync_map_file()

    if progress_callback:
        progress_callback(0.9)

    with open(output_file, "r", encoding="utf-8") as f:
        sync_data = json.load(f)

    result = []
    for fragment in sync_data.get("fragments", []):
        text = fragment.get("lines", [""])[0] if fragment.get("lines") else ""
        if not text or text == "SIL":
            continue
        result.append({
            "word": text,
            "start": float(fragment["begin"]),
            "end": float(fragment["end"]),
        })

    Path(text_file).unlink(missing_ok=True)
    Path(output_file).unlink(missing_ok=True)
    if wav_path != audio_path:
        Path(wav_path).unlink(missing_ok=True)

    if progress_callback:
        progress_callback(1.0)

    return result


def _energy_based_align(words: list[str], audio_path: str, progress_callback=None) -> list[dict]:
    wav_path = audio_path
    if not audio_path.endswith(".wav"):
        try:
            wav_path = extract_audio_to_wav(audio_path)
        except Exception:
            return _simple_duration_align(words, audio_path)

    if progress_callback:
        progress_callback(0.1)

    samples, sample_rate = _read_wav(wav_path)
    if samples is None:
        return _simple_duration_align(words, audio_path)

    if progress_callback:
        progress_callback(0.2)

    hop_sec = HOP_MS / 1000.0
    energy = _compute_energy(samples, sample_rate, frame_ms=FRAME_MS, hop_ms=HOP_MS)

    if progress_callback:
        progress_callback(0.4)

    speech_regions = _detect_speech_regions(energy, hop_sec)

    if not speech_regions:
        duration = len(samples) / sample_rate
        speech_regions = [(0.0, duration)]

    if progress_callback:
        progress_callback(0.5)

    result = _align_words_to_regions(words, speech_regions, energy, hop_sec)

    if progress_callback:
        progress_callback(1.0)

    if wav_path != audio_path:
        Path(wav_path).unlink(missing_ok=True)

    return result


def _read_wav(wav_path: str):
    try:
        with wave.open(wav_path, "r") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)
    except Exception:
        return None, None

    if sampwidth == 2:
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    elif sampwidth == 1:
        samples = np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0
    elif sampwidth == 4:
        samples = np.frombuffer(raw, dtype=np.int32).astype(np.float32)
    else:
        return None, None

    if n_channels > 1:
        samples = samples.reshape(-1, n_channels).mean(axis=1)

    max_val = np.abs(samples).max()
    if max_val > 0:
        samples = samples / max_val

    return samples, framerate


def _compute_energy(samples: np.ndarray, sample_rate: int, frame_ms: int = 25, hop_ms: int = 10) -> np.ndarray:
    frame_len = int(sample_rate * frame_ms / 1000)
    hop_len = int(sample_rate * hop_ms / 1000)
    n_frames = max(1, (len(samples) - frame_len) // hop_len + 1)

    energy = np.zeros(n_frames, dtype=np.float32)
    for i in range(n_frames):
        start = i * hop_len
        frame = samples[start:start + frame_len]
        energy[i] = np.sqrt(np.mean(frame ** 2))

    return energy


def _detect_speech_regions(
    energy: np.ndarray,
    hop_sec: float,
    silence_threshold_ratio: float = 0.04,
    min_silence_duration: float = 0.20,
    min_speech_duration: float = 0.08,
) -> list[tuple[float, float]]:
    if len(energy) == 0:
        return []

    smoothed = medfilt(energy, kernel_size=5)
    threshold = smoothed.max() * silence_threshold_ratio
    is_speech = smoothed > threshold

    min_silence_frames = int(min_silence_duration / hop_sec)
    min_speech_frames = int(min_speech_duration / hop_sec)

    regions = []
    in_speech = False
    region_start = 0
    silence_count = 0

    for i, s in enumerate(is_speech):
        if s:
            if not in_speech:
                region_start = i
                in_speech = True
            silence_count = 0
        else:
            if in_speech:
                silence_count += 1
                if silence_count >= min_silence_frames:
                    region_end = i - silence_count
                    if region_end - region_start >= min_speech_frames:
                        regions.append((region_start * hop_sec, region_end * hop_sec))
                    in_speech = False
                    silence_count = 0

    if in_speech:
        region_end = len(energy) - 1
        if region_end - region_start >= min_speech_frames:
            regions.append((region_start * hop_sec, region_end * hop_sec))

    return regions


def _align_words_to_regions(
    words: list[str],
    regions: list[tuple[float, float]],
    energy: np.ndarray,
    hop_sec: float,
) -> list[dict]:
    """
    Assign words to regions proportionally, then within each region use
    DP boundary detection for precise per-word timing.
    """
    total_chars = sum(len(w) for w in words)
    total_speech_time = sum(end - start for start, end in regions)

    if total_chars == 0 or total_speech_time == 0:
        return []

    result = []
    word_idx = 0
    n_regions = len(regions)

    for region_idx, (region_start, region_end) in enumerate(regions):
        is_last_region = (region_idx == n_regions - 1)

        if is_last_region:
            # Last region gets all remaining words
            region_words = words[word_idx:]
            word_idx = len(words)
        else:
            region_duration = region_end - region_start
            region_char_budget = total_chars * (region_duration / total_speech_time)

            region_words = []
            region_chars_used = 0
            while word_idx < len(words) and region_chars_used + len(words[word_idx]) <= region_char_budget + 1.0:
                region_words.append(words[word_idx])
                region_chars_used += len(words[word_idx])
                word_idx += 1

            if not region_words and word_idx < len(words):
                region_words.append(words[word_idx])
                word_idx += 1

        if not region_words:
            continue

        aligned = _align_within_region(region_words, region_start, region_end, energy, hop_sec)
        result.extend(aligned)

    return result


def _align_within_region(
    words: list[str],
    region_start: float,
    region_end: float,
    energy: np.ndarray,
    hop_sec: float,
) -> list[dict]:
    """
    Within a speech region, find word boundaries by:
    1. Detect all energy dips (candidate boundaries)
    2. Use DP to select N-1 best boundaries for N words, optimizing for
       boundary quality (dip depth) and duration consistency
    """
    n_words = len(words)
    if n_words == 1:
        return [{"word": words[0], "start": round(region_start, 3), "end": round(region_end, 3)}]

    frame_start = int(region_start / hop_sec)
    frame_end = int(region_end / hop_sec)
    frame_end = min(frame_end, len(energy))
    frame_start = max(0, frame_start)
    n_frames = frame_end - frame_start

    if n_frames < n_words * 2:
        return _uniform_by_char(words, region_start, region_end)

    region_energy = energy[frame_start:frame_end].copy()

    # Compute boundary quality at each frame (how good a split point it is)
    boundary_quality = _compute_boundary_quality(region_energy)

    # Estimate expected duration per word: Chinese syllables ~200-400ms
    # Weight slightly by character count but mostly uniform
    char_counts = [len(w) for w in words]
    total_chars = sum(char_counts)
    region_dur = region_end - region_start

    # Expected duration: blend between uniform and char-proportional
    # Chinese speech is mostly syllable-timed, so bias toward uniform
    uniform_dur = region_dur / n_words
    expected_durs = []
    for cc in char_counts:
        char_dur = (cc / total_chars) * region_dur
        # 70% uniform + 30% char-proportional
        expected_durs.append(uniform_dur * 0.7 + char_dur * 0.3)

    # Find optimal boundaries using DP
    boundaries = _dp_boundaries(boundary_quality, expected_durs, n_frames, hop_sec)

    # Convert to result
    result = []
    prev_time = region_start
    for i, word in enumerate(words):
        if i < len(boundaries):
            end_time = region_start + boundaries[i] * hop_sec
        else:
            end_time = region_end
        end_time = max(prev_time + 0.01, min(end_time, region_end))
        result.append({"word": word, "start": round(prev_time, 3), "end": round(end_time, 3)})
        prev_time = end_time

    return result


def _compute_boundary_quality(region_energy: np.ndarray) -> np.ndarray:
    """
    For each frame, compute how good a word boundary it would be.
    High quality = energy dip relative to neighbors.
    """
    n = len(region_energy)
    quality = np.zeros(n, dtype=np.float32)

    # Smooth for stability
    kernel = min(5, n if n % 2 == 1 else n - 1)
    if kernel >= 3:
        smooth = medfilt(region_energy, kernel_size=kernel)
    else:
        smooth = region_energy.copy()

    # For each frame, measure how much it's a local minimum
    window = max(2, min(8, n // 10))
    for i in range(window, n - window):
        left_max = smooth[i - window:i].max()
        right_max = smooth[i + 1:i + window + 1].max()
        local_val = smooth[i]
        # Dip depth: how far below the surrounding maxima
        depth = (left_max + right_max) / 2 - local_val
        quality[i] = max(0, depth)

    # Normalize
    qmax = quality.max()
    if qmax > 0:
        quality /= qmax

    return quality


def _dp_boundaries(
    boundary_quality: np.ndarray,
    expected_durs: list[float],
    n_frames: int,
    hop_sec: float,
) -> list[int]:
    """
    Find N-1 boundary positions that maximize boundary quality
    while keeping segment durations close to expected.
    Uses DP with pruned search space.
    """
    n_words = len(expected_durs)
    n_boundaries = n_words - 1

    if n_boundaries == 0:
        return []

    # Build cumulative expected durations (in frames) for target positions
    cum_dur = []
    t = 0.0
    for d in expected_durs[:-1]:
        t += d
        cum_dur.append(int(t / hop_sec))

    # Search around each target position ±40% of segment duration
    search_ranges = []
    for i, target in enumerate(cum_dur):
        margin = max(5, int(expected_durs[i] / hop_sec * 0.5))
        lo = max(2, target - margin)
        hi = min(n_frames - 2, target + margin)
        search_ranges.append((lo, hi))

    # Greedy selection with local optimization
    boundaries = []
    prev_bound = 0

    for i in range(n_boundaries):
        lo, hi = search_ranges[i]
        lo = max(lo, prev_bound + 2)
        if lo >= hi:
            lo = prev_bound + 2
            hi = lo + 5

        # Score each candidate: blend of boundary quality and position accuracy
        best_score = -float('inf')
        best_pos = cum_dur[i]

        for pos in range(lo, min(hi + 1, n_frames)):
            # Quality score from energy dip
            q_score = boundary_quality[pos] if pos < len(boundary_quality) else 0

            # Duration accuracy: how close to target
            target = cum_dur[i]
            dist = abs(pos - target)
            max_dist = max(1, hi - lo)
            d_score = 1.0 - (dist / max_dist)

            # Combined score
            score = q_score * 0.6 + d_score * 0.4

            if score > best_score:
                best_score = score
                best_pos = pos

        boundaries.append(best_pos)
        prev_bound = best_pos

    return boundaries


def _energy_weighted_distribute(
    words: list[str],
    region_start: float,
    region_end: float,
    region_energy: np.ndarray,
    hop_sec: float,
) -> list[dict]:
    """
    Distribute words using cumulative energy as a time warping function.
    Words with more characters get proportionally more energy-time.
    """
    n = len(region_energy)
    if n == 0:
        return _uniform_by_char(words, region_start, region_end)

    # Cumulative energy (normalized to 0..1)
    cum_energy = np.cumsum(region_energy)
    total_energy = cum_energy[-1]
    if total_energy == 0:
        return _uniform_by_char(words, region_start, region_end)
    cum_energy = cum_energy / total_energy

    # Each word gets a share of total energy proportional to char count
    total_chars = sum(len(w) for w in words)
    result = []
    energy_cursor = 0.0

    for word in words:
        char_share = len(word) / total_chars
        energy_target = energy_cursor + char_share

        # Find frame where cumulative energy reaches target
        start_frame = np.searchsorted(cum_energy, energy_cursor)
        end_frame = np.searchsorted(cum_energy, energy_target)

        start_time = region_start + start_frame * hop_sec
        end_time = region_start + end_frame * hop_sec

        # Clamp
        start_time = max(region_start, min(start_time, region_end))
        end_time = max(start_time + 0.01, min(end_time, region_end))

        result.append({"word": word, "start": round(start_time, 3), "end": round(end_time, 3)})
        energy_cursor = energy_target

    return result


def _uniform_by_char(words: list[str], region_start: float, region_end: float) -> list[dict]:
    total_chars = sum(len(w) for w in words)
    if total_chars == 0:
        return []
    duration = region_end - region_start
    result = []
    t = region_start
    for w in words:
        d = (len(w) / total_chars) * duration
        result.append({"word": w, "start": round(t, 3), "end": round(t + d, 3)})
        t += d
    return result


def _simple_duration_align(words: list[str], audio_path: str) -> list[dict]:
    try:
        duration = get_audio_duration(audio_path)
    except Exception:
        duration = len(words) * 0.5

    total_chars = sum(len(w) for w in words)
    if total_chars == 0:
        return []

    result = []
    t = 0.0
    for w in words:
        w_dur = (len(w) / total_chars) * duration
        result.append({"word": w, "start": round(t, 3), "end": round(t + w_dur, 3)})
        t += w_dur
    return result
