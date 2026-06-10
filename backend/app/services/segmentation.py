PUNCTUATION_SPLIT = set("。，！？；：、")


def segment_words(
    words: list[dict],
    max_chars: int = 18,
    min_pause: float = 0.3,
) -> list[dict]:
    if not words:
        return []

    segments = []
    current_words = []
    current_text = ""

    for i, word in enumerate(words):
        w = word["word"]

        would_exceed = len(current_text) + len(w) > max_chars and current_text
        has_pause = (
            i > 0
            and word["start"] - words[i - 1]["end"] >= min_pause
            and current_words
        )

        if would_exceed or has_pause:
            if current_words:
                segments.append(_make_segment(current_words, current_text))
            current_words = []
            current_text = ""

        current_words.append(word)
        current_text += w

        if any(w.endswith(p) for p in PUNCTUATION_SPLIT):
            segments.append(_make_segment(current_words, current_text))
            current_words = []
            current_text = ""

    if current_words:
        segments.append(_make_segment(current_words, current_text))

    segments = _merge_short_segments(segments, min_duration=0.5)
    return segments


def _make_segment(words: list[dict], text: str) -> dict:
    return {
        "text": text,
        "start_time": words[0]["start"],
        "end_time": words[-1]["end"],
        "words": words,
    }


def _merge_short_segments(segments: list[dict], min_duration: float) -> list[dict]:
    if len(segments) <= 1:
        return segments

    merged = [segments[0]]
    for seg in segments[1:]:
        duration = seg["end_time"] - seg["start_time"]
        if duration < min_duration and merged:
            prev = merged[-1]
            prev["text"] += seg["text"]
            prev["end_time"] = seg["end_time"]
            prev["words"].extend(seg["words"])
        else:
            merged.append(seg)

    return merged
