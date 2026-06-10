import json

MIN_GAP = 0.05


def apply_global_shift(subtitles: list, offset_seconds: float):
    for sub in subtitles:
        sub.start_time = max(0.0, sub.start_time + offset_seconds)
        sub.end_time = max(0.0, sub.end_time + offset_seconds)
        if sub.words_json:
            words = json.loads(sub.words_json)
            for w in words:
                w["start"] = max(0.0, w["start"] + offset_seconds)
                w["end"] = max(0.0, w["end"] + offset_seconds)
            sub.words_json = json.dumps(words, ensure_ascii=False)


def apply_linear_scale(subtitles: list, factor: float, anchor_time: float = 0.0):
    for sub in subtitles:
        sub.start_time = anchor_time + (sub.start_time - anchor_time) * factor
        sub.end_time = anchor_time + (sub.end_time - anchor_time) * factor
        if sub.words_json:
            words = json.loads(sub.words_json)
            for w in words:
                w["start"] = anchor_time + (w["start"] - anchor_time) * factor
                w["end"] = anchor_time + (w["end"] - anchor_time) * factor
            sub.words_json = json.dumps(words, ensure_ascii=False)


def adjust_with_propagation(subtitles: list, target_line_id: int, new_start: float, new_end: float):
    sub_map = {s.id: s for s in subtitles}
    ordered = sorted(subtitles, key=lambda s: s.index)

    target = sub_map.get(target_line_id)
    if not target:
        return

    target.start_time = new_start
    target.end_time = new_end

    target_idx = next(i for i, s in enumerate(ordered) if s.id == target_line_id)

    for i in range(target_idx - 1, max(target_idx - 4, -1), -1):
        prev = ordered[i]
        current = ordered[i + 1]
        if prev.end_time > current.start_time - MIN_GAP:
            prev.end_time = current.start_time - MIN_GAP
            if prev.end_time < prev.start_time + MIN_GAP:
                prev.start_time = prev.end_time - MIN_GAP
                if prev.start_time < 0:
                    prev.start_time = 0
                    prev.end_time = MIN_GAP

    for i in range(target_idx + 1, min(target_idx + 4, len(ordered))):
        prev = ordered[i - 1]
        current = ordered[i]
        if current.start_time < prev.end_time + MIN_GAP:
            current.start_time = prev.end_time + MIN_GAP
            if current.start_time > current.end_time - MIN_GAP:
                current.end_time = current.start_time + MIN_GAP
