from dataclasses import dataclass
from typing import Iterable, List, Optional
from pycaps.common import Document, Segment, Line, Word, TimeFragment
from pycaps.logger import logger

MIN_DURATION = 0.01

@dataclass
class WhisperWord:
    text: str
    start: float
    end: float

@dataclass
class WhisperSegment:
    text: str
    start: float
    end: float
    words: Optional[List[WhisperWord]]

def build_document(segments: Iterable[WhisperSegment]) -> Document:
    """
    Creates a Document from the segments returned by a Whisper implementation (openai-whisper, faster-whisper, etc.).
    """
    document = Document()
    for segment_info in segments:
        segment_time = _create_time_fragment(segment_info.start, segment_info.end)
        segment = Segment(time=segment_time)
        line = Line(time=segment_time)
        segment.lines.add(line)

        if segment_info.words is None:
            logger().debug(f"Segment '{segment_info.text}' has no detailed word data.")
            continue

        for word_info in segment_info.words:
            # Ensure 'word' is a string, sometimes Whisper might return non-string for certain symbols.
            word_text = str(word_info.text).strip()
            if not word_text:
                continue

            word = Word(text=word_text, time=_create_time_fragment(word_info.start, word_info.end))
            line.words.add(word) # so far is everything in one single line (we split it in next steps of the pipeline)

        document.segments.add(segment)

    if not document.segments:
        logger().warning("No valid segments were processed from Whisper's transcription.")

    return document

def _create_time_fragment(start: float, end: float) -> TimeFragment:
    start = float(start)
    end = float(end)
    if start == end:
        end = start + MIN_DURATION
    return TimeFragment(start=start, end=end)
