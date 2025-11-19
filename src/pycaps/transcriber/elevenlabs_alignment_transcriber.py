import json
from typing import Optional, Union, Any
from .base_transcriber import AudioTranscriber
from pycaps.common import Document, Segment, Line, Word, TimeFragment
from pycaps.logger import logger


class ElevenLabsAlignmentTranscriber(AudioTranscriber):
    """
    Transcriber that uses alignment data from Eleven Labs Text-to-Speech API.

    This transcriber converts character-level timing information from Eleven Labs
    into word-level timing that can be used by pycaps.

    The alignment data should be in the format returned by Eleven Labs API:
    {
        "alignment": {
            "characters": ["H", "e", "l", "l", "o"],
            "character_start_times_seconds": [0.0, 0.1, 0.2, 0.3, 0.4],
            "character_end_times_seconds": [0.1, 0.2, 0.3, 0.4, 0.5]
        },
        "normalized_alignment": {
            "characters": [" ", "H", "e", "l", "l", "o", " "],
            "character_start_times_seconds": [0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.45],
            "character_end_times_seconds": [0.05, 0.1, 0.2, 0.3, 0.4, 0.45, 0.5]
        }
    }
    """

    def __init__(self, alignment_data: Optional[Union[dict, str]] = None):
        """
        Initialize the Eleven Labs alignment transcriber.

        Args:
            alignment_data: Either a dictionary containing alignment data from Eleven Labs,
                          or a path to a JSON file containing the alignment data.
                          If None, the transcribe method will require a path to be provided.
        """
        self._alignment_data = alignment_data

    def transcribe(self, audio_path: str) -> Document:
        """
        Creates a Document from Eleven Labs alignment data.

        Note: The audio_path parameter is not used for actual transcription,
        but is kept for compatibility with the AudioTranscriber interface.
        The alignment data should be provided during initialization.

        Args:
            audio_path: Path to the audio file (not used, kept for interface compatibility)

        Returns:
            A Document object with word-level timing information.
        """
        alignment_data = self._load_alignment_data()

        if not alignment_data:
            logger().warning("No alignment data provided for ElevenLabsAlignmentTranscriber.")
            return Document()

        # Prefer normalized_alignment if available, otherwise use alignment
        alignment = alignment_data.get("normalized_alignment") or alignment_data.get("alignment")

        if not alignment:
            logger().warning("No alignment or normalized_alignment found in Eleven Labs data.")
            return Document()

        return self._parse_alignment(alignment)

    def _load_alignment_data(self) -> Optional[dict]:
        """Load alignment data from file path or return dict directly."""
        if self._alignment_data is None:
            return None

        if isinstance(self._alignment_data, dict):
            return self._alignment_data

        if isinstance(self._alignment_data, str):
            try:
                with open(self._alignment_data, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger().error(f"Error loading Eleven Labs alignment file: {e}")
                return None

        return None

    def _parse_alignment(self, alignment: dict) -> Document:
        """
        Parse alignment data and create Document with word-level timing.

        Args:
            alignment: Dictionary containing characters and their timing information.

        Returns:
            Document with parsed word timing.
        """
        characters = alignment.get("characters", [])
        start_times = alignment.get("character_start_times_seconds", [])
        end_times = alignment.get("character_end_times_seconds", [])

        if not characters or not start_times or not end_times:
            logger().warning("Empty alignment data from Eleven Labs.")
            return Document()

        if len(characters) != len(start_times) or len(characters) != len(end_times):
            logger().warning("Mismatched lengths in Eleven Labs alignment data.")
            return Document()

        # Convert character-level timing to word-level timing
        words_data = self._characters_to_words(characters, start_times, end_times)

        if not words_data:
            logger().warning("No words extracted from Eleven Labs alignment data.")
            return Document()

        # Create document structure
        document = Document()

        # Calculate segment timing from first and last word
        segment_start = words_data[0]["start"]
        segment_end = words_data[-1]["end"]

        if segment_start == segment_end:
            segment_end = segment_start + 0.01

        segment_time = TimeFragment(start=segment_start, end=segment_end)
        segment = Segment(time=segment_time)
        line = Line(time=segment_time)
        segment.lines.add(line)

        # Add words to line
        for word_data in words_data:
            word_start = word_data["start"]
            word_end = word_data["end"]

            if word_start == word_end:
                word_end = word_start + 0.01

            word_time = TimeFragment(start=word_start, end=word_end)
            word = Word(text=word_data["text"], time=word_time)
            line.words.add(word)

        document.segments.add(segment)

        logger().debug(f"Parsed {len(words_data)} words from Eleven Labs alignment data.")

        return document

    def _characters_to_words(self, characters: list, start_times: list, end_times: list) -> list:
        """
        Convert character-level timing to word-level timing.

        Words are separated by spaces. Each word's timing is determined by
        the start time of its first character and end time of its last character.

        Args:
            characters: List of characters
            start_times: List of start times for each character
            end_times: List of end times for each character

        Returns:
            List of dictionaries with word text, start, and end times.
        """
        words = []
        current_word_chars = []
        current_word_start = None
        current_word_end = None

        for i, char in enumerate(characters):
            if char == " " or char == "\n" or char == "\t":
                # End of word - save it if we have characters
                if current_word_chars:
                    word_text = "".join(current_word_chars).strip()
                    if word_text:
                        words.append({
                            "text": word_text,
                            "start": current_word_start,
                            "end": current_word_end
                        })
                    current_word_chars = []
                    current_word_start = None
                    current_word_end = None
            else:
                # Add character to current word
                if current_word_start is None:
                    current_word_start = start_times[i]
                current_word_end = end_times[i]
                current_word_chars.append(char)

        # Don't forget the last word
        if current_word_chars:
            word_text = "".join(current_word_chars).strip()
            if word_text:
                words.append({
                    "text": word_text,
                    "start": current_word_start,
                    "end": current_word_end
                })

        return words
