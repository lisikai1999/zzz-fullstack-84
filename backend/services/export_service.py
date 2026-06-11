from typing import List, Dict

from utils.time_format import seconds_to_srt_time, seconds_to_vtt_time, seconds_to_ass_time


def export_srt(subtitles: List[Dict]) -> str:
    lines = []
    for s in subtitles:
        lines.append(str(s["index"]))
        lines.append(f"{seconds_to_srt_time(s['start_time'])} --> {seconds_to_srt_time(s['end_time'])}")
        lines.append(s["text"])
        lines.append("")
    return "\n".join(lines)


def export_vtt(subtitles: List[Dict]) -> str:
    lines = ["WEBVTT", ""]
    for s in subtitles:
        lines.append(f"{seconds_to_vtt_time(s['start_time'])} --> {seconds_to_vtt_time(s['end_time'])}")
        lines.append(s["text"])
        lines.append("")
    return "\n".join(lines)


def export_ass(subtitles: List[Dict]) -> str:
    header = """[Script Info]
Title: Subtitle Export
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei,48,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for s in subtitles:
        start = seconds_to_ass_time(s["start_time"])
        end = seconds_to_ass_time(s["end_time"])
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{s['text']}")
    return "\n".join(lines)
