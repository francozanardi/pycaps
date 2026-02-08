from enum import Enum


class TranscriptFormat(str, Enum):
    AUTO = "auto"
    WHISPER_JSON = "whisper_json"
    PYCAPS_JSON = "pycaps_json"
    SRT = "srt"
    VTT = "vtt"
