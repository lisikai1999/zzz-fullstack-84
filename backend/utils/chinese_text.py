import re
from typing import List, Optional

try:
    import jieba
except ImportError:
    jieba = None

SENTENCE_END_PUNCTUATION = set("。！？!?")
CLAUSE_PUNCTUATION = set("，、；：,;:")
ALL_PUNCTUATION = SENTENCE_END_PUNCTUATION | CLAUSE_PUNCTUATION | set('“”‘’"\'()（）【】《》')


def segment_chinese(text: str) -> List[str]:
    """Segment Chinese text into words using jieba."""
    if jieba is None:
        return list(text)
    return list(jieba.cut(text))


def is_punctuation(char: str) -> bool:
    return char in ALL_PUNCTUATION


def is_sentence_end(char: str) -> bool:
    return char in SENTENCE_END_PUNCTUATION


def is_clause_break(char: str) -> bool:
    return char in CLAUSE_PUNCTUATION


def find_split_points(text: str, max_chars: int = 20) -> List[int]:
    """Find optimal split points in text based on punctuation.
    Returns character indices where splits should occur (after the character)."""
    if len(text) <= max_chars:
        return []

    split_points = []
    last_split = 0

    for i, char in enumerate(text):
        segment_len = i - last_split + 1
        if segment_len >= max_chars:
            best = _find_best_break(text, last_split, i)
            if best is not None:
                split_points.append(best)
                last_split = best + 1
            else:
                split_points.append(i)
                last_split = i + 1

    return split_points


def _find_best_break(text: str, start: int, end: int) -> Optional[int]:
    """Find the best break point between start and end, preferring punctuation."""
    for i in range(end, start, -1):
        if is_sentence_end(text[i]):
            return i
    for i in range(end, start, -1):
        if is_clause_break(text[i]):
            return i
    return None
