from enum import Enum
from typing import List

class VideoQuality(str, Enum):
    LOW = "low"
    MIDDLE = "middle"
    HIGH = "high"
    VERY_HIGH = "very_high"

class CacheStrategy(str, Enum):
    CSS_CLASSES_AWARE = "css-classes-aware" # two words with same CSS classes, same text are considered equal (word position on line is ignored)
    POSITION_AWARE = "position-aware" # two words with same CSS classes + same texts, need to have same position on line to be considered equals (useful when line has things like gradient)
    NONE = "none" # do not use cache -> if two words with same position, CSS classes, and text can be different, so you have to choose this

class AspectRatio(str, Enum):
    VERTICAL = "9:16"
    HORIZONTAL = "16:9"
    SQUARE = "1:1"
    PORTRAIT_FEED = "4:5"

class ElementType(str, Enum):
    WORD = "word"
    LINE = "line"
    SEGMENT = "segment"

class EventType(str, Enum):
    ON_NARRATION_STARTS = "narration-starts"
    ON_NARRATION_ENDS = "narration-ends"

class ElementState(str, Enum):
    WORD_BEING_NARRATED = "word-being-narrated"
    WORD_NOT_NARRATED_YET = "word-not-narrated-yet"
    WORD_ALREADY_NARRATED = "word-already-narrated"

    LINE_BEING_NARRATED = "line-being-narrated"
    LINE_NOT_NARRATED_YET = "line-not-narrated-yet"
    LINE_ALREADY_NARRATED = "line-already-narrated"
    
    @staticmethod
    def get_all_line_states() -> List['ElementState']:
        return [
            ElementState.LINE_NOT_NARRATED_YET,
            ElementState.LINE_BEING_NARRATED,
            ElementState.LINE_ALREADY_NARRATED,
        ]
    
    @staticmethod
    def get_all_word_states() -> List['ElementState']:
        return [
            ElementState.WORD_NOT_NARRATED_YET,
            ElementState.WORD_BEING_NARRATED,
            ElementState.WORD_ALREADY_NARRATED,
        ]
    
    @staticmethod
    def get_all_valid_states_combinations() -> List[List['ElementState']]:
        return [
            [ElementState.LINE_NOT_NARRATED_YET, ElementState.WORD_NOT_NARRATED_YET],
            [ElementState.LINE_BEING_NARRATED, ElementState.WORD_NOT_NARRATED_YET],
            [ElementState.LINE_BEING_NARRATED, ElementState.WORD_BEING_NARRATED],
            [ElementState.LINE_BEING_NARRATED, ElementState.WORD_ALREADY_NARRATED],
            [ElementState.LINE_ALREADY_NARRATED, ElementState.WORD_ALREADY_NARRATED],
        ]
