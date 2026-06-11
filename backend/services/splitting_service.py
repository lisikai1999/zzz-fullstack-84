from typing import List, Dict, Optional

from utils.chinese_text import is_sentence_end, is_clause_break, is_punctuation


def split_alignment_to_subtitles(
    word_alignments: List[Dict],
    max_chars: int = 20,
    pause_threshold_ms: float = 300.0,
) -> List[Dict]:
    """
    Split word-level alignments into subtitle lines.
    Priority: sentence-end punctuation > clause punctuation > pause > max_chars.
    """
    if not word_alignments:
        return []

    subtitles = []
    current_chars = []
    current_start = word_alignments[0]["start"]

    for i, item in enumerate(word_alignments):
        current_chars.append(item)

        should_split = False
        text_so_far = "".join(c["char"] for c in current_chars)

        if is_sentence_end(item["char"]):
            should_split = True
        elif len(text_so_far) >= max_chars:
            split_idx = _find_best_split_in_group(current_chars)
            if split_idx is not None and split_idx < len(current_chars) - 1:
                before = current_chars[: split_idx + 1]
                after = current_chars[split_idx + 1:]
                subtitles.append(_make_subtitle(before, current_start))
                current_chars = after
                current_start = after[0]["start"]
                continue
            else:
                should_split = True
        elif is_clause_break(item["char"]) and len(text_so_far) >= max_chars * 0.5:
            should_split = True
        elif i + 1 < len(word_alignments):
            gap_ms = (word_alignments[i + 1]["start"] - item["end"]) * 1000
            if gap_ms >= pause_threshold_ms and len(text_so_far) >= 4:
                should_split = True

        if should_split and current_chars:
            subtitles.append(_make_subtitle(current_chars, current_start))
            current_chars = []
            if i + 1 < len(word_alignments):
                current_start = word_alignments[i + 1]["start"]

    if current_chars:
        subtitles.append(_make_subtitle(current_chars, current_start))

    return subtitles


def _make_subtitle(chars: List[Dict], fallback_start: float) -> Dict:
    text = "".join(c["char"] for c in chars)
    start = chars[0]["start"] if chars else fallback_start
    end = chars[-1]["end"] if chars else fallback_start
    return {"text": text, "start_time": start, "end_time": end}


def _find_best_split_in_group(chars: List[Dict]) -> Optional[int]:
    """Find best split point in a group, preferring punctuation near the middle."""
    n = len(chars)
    mid = n // 2

    for radius in range(n // 2):
        for offset in [radius, -radius]:
            idx = mid + offset
            if 0 <= idx < n and is_clause_break(chars[idx]["char"]):
                return idx

    for radius in range(n // 2):
        for offset in [radius, -radius]:
            idx = mid + offset
            if 0 <= idx < n and is_punctuation(chars[idx]["char"]):
                return idx

    return None
