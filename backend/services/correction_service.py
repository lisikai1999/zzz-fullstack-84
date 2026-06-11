from typing import List, Dict

from schemas.correction import CorrectionRequest
from config import settings


def apply_correction(subtitles: List[Dict], req: CorrectionRequest) -> List[Dict]:
    """Apply batch correction to subtitle timestamps."""
    if req.mode == "global_shift":
        return _global_shift(subtitles, req.offset_ms or 0)
    elif req.mode == "linear_scale":
        return _linear_scale(subtitles, req.scale_factor or 1.0, req.scale_offset or 0)
    elif req.mode == "single_cascade":
        return _single_cascade(subtitles, req.anchor_index or 0, req.new_start or 0)
    elif req.mode == "anchor_interpolation":
        return _anchor_interpolation(subtitles, req.anchors or [])
    return subtitles


def _global_shift(subtitles: List[Dict], offset_ms: float) -> List[Dict]:
    offset_sec = offset_ms / 1000.0
    result = []
    for s in subtitles:
        result.append({
            **s,
            "start_time": max(0, s["start_time"] + offset_sec),
            "end_time": max(0, s["end_time"] + offset_sec),
        })
    return result


def _linear_scale(subtitles: List[Dict], factor: float, offset: float) -> List[Dict]:
    result = []
    for s in subtitles:
        result.append({
            **s,
            "start_time": max(0, s["start_time"] * factor + offset),
            "end_time": max(0, s["end_time"] * factor + offset),
        })
    return result


def _single_cascade(subtitles: List[Dict], anchor_index: int, new_start: float) -> List[Dict]:
    """Adjust one subtitle's start time and cascade proportionally to neighbors."""
    if anchor_index < 0 or anchor_index >= len(subtitles):
        return subtitles

    result = [dict(s) for s in subtitles]
    target = result[anchor_index]
    old_start = target["start_time"]
    shift = new_start - old_start
    duration = target["end_time"] - target["start_time"]

    target["start_time"] = new_start
    target["end_time"] = new_start + duration

    min_duration = settings.MIN_SUBTITLE_DURATION_MS / 1000.0

    if shift > 0 and anchor_index + 1 < len(result):
        _cascade_forward(result, anchor_index, min_duration)
    elif shift < 0 and anchor_index > 0:
        _cascade_backward(result, anchor_index, min_duration)

    return result


def _cascade_forward(subtitles: List[Dict], from_idx: int, min_duration: float):
    for i in range(from_idx + 1, len(subtitles)):
        prev_end = subtitles[i - 1]["end_time"]
        if subtitles[i]["start_time"] < prev_end:
            duration = max(min_duration, subtitles[i]["end_time"] - subtitles[i]["start_time"])
            subtitles[i]["start_time"] = prev_end
            subtitles[i]["end_time"] = prev_end + duration
        else:
            break


def _cascade_backward(subtitles: List[Dict], from_idx: int, min_duration: float):
    for i in range(from_idx - 1, -1, -1):
        next_start = subtitles[i + 1]["start_time"]
        if subtitles[i]["end_time"] > next_start:
            duration = max(min_duration, subtitles[i]["end_time"] - subtitles[i]["start_time"])
            subtitles[i]["end_time"] = next_start
            subtitles[i]["start_time"] = max(0, next_start - duration)
        else:
            break


def _anchor_interpolation(subtitles: List[Dict], anchors) -> List[Dict]:
    """Multi-anchor piecewise linear interpolation."""
    if not anchors or len(anchors) < 2:
        return subtitles

    anchors_sorted = sorted(anchors, key=lambda a: a.subtitle_index)
    result = [dict(s) for s in subtitles]

    for seg_idx in range(len(anchors_sorted) - 1):
        a1 = anchors_sorted[seg_idx]
        a2 = anchors_sorted[seg_idx + 1]

        idx1, idx2 = a1.subtitle_index, a2.subtitle_index
        if idx1 >= idx2 or idx1 >= len(subtitles) or idx2 >= len(subtitles):
            continue

        old_start1 = subtitles[idx1]["start_time"]
        old_start2 = subtitles[idx2]["start_time"]
        new_start1 = a1.correct_start
        new_start2 = a2.correct_start

        old_range = old_start2 - old_start1
        if old_range <= 0:
            continue

        for i in range(idx1, idx2 + 1):
            fraction = (subtitles[i]["start_time"] - old_start1) / old_range
            new_time = new_start1 + fraction * (new_start2 - new_start1)
            duration = subtitles[i]["end_time"] - subtitles[i]["start_time"]
            result[i]["start_time"] = max(0, round(new_time, 3))
            result[i]["end_time"] = max(0, round(new_time + duration, 3))

    return result
