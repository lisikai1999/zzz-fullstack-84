from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

_model = None
_stable_ts_available = None


def check_stable_ts() -> bool:
    """Check if stable-ts is importable. Cached after first call."""
    global _stable_ts_available
    if _stable_ts_available is None:
        try:
            import stable_whisper  # noqa: F401
            _stable_ts_available = True
        except ImportError:
            _stable_ts_available = False
    return _stable_ts_available


def get_whisper_model():
    global _model
    if _model is None:
        if not check_stable_ts():
            raise RuntimeError(
                "对齐引擎未安装。请执行: pip install stable-ts openai-whisper\n"
                "GPU加速还需安装对应版本的PyTorch: https://pytorch.org/get-started/locally/"
            )
        import stable_whisper
        from config import settings
        logger.info(f"Loading Whisper model: {settings.WHISPER_MODEL}")
        _model = stable_whisper.load_model(settings.WHISPER_MODEL)
    return _model


def align_audio_with_text(audio_path: str, text: str, language: str = "zh") -> List[Dict]:
    """
    Perform forced alignment of text against audio using stable-ts.
    Raises RuntimeError if stable-ts/whisper is not installed.
    """
    model = get_whisper_model()
    result = model.align(audio_path, text, language=language)

    word_alignments = []
    for segment in result.segments:
        for word in segment.words:
            for char in word.word.strip():
                word_alignments.append({
                    "char": char,
                    "start": round(word.start, 3),
                    "end": round(word.end, 3),
                    "confidence": round(getattr(word, "probability", 0.9), 3),
                })

    if language == "zh":
        word_alignments = _distribute_char_timestamps(word_alignments)

    return word_alignments


def _distribute_char_timestamps(alignments: List[Dict]) -> List[Dict]:
    """For grouped characters sharing the same timestamp, distribute evenly."""
    result = []
    i = 0
    while i < len(alignments):
        group = [alignments[i]]
        j = i + 1
        while j < len(alignments) and alignments[j]["start"] == alignments[i]["start"]:
            group.append(alignments[j])
            j += 1

        if len(group) > 1:
            start = group[0]["start"]
            end = group[0]["end"]
            duration = end - start
            step = duration / len(group) if len(group) > 0 else 0
            for k, item in enumerate(group):
                item["start"] = round(start + k * step, 3)
                item["end"] = round(start + (k + 1) * step, 3)

        result.extend(group)
        i = j

    return result
