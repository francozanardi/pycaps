from ..effect import Effect
from pycaps.tag import TagCondition
from typing import Optional
from .sound import Sound
from pycaps.common import Document, ElementType, EventType, TimeFragment, Word, Line, Segment
from typing import List, Union

class SoundEffect(Effect):
    def __init__(
            self,
            sound: Sound,
            when: EventType,
            what: ElementType,
            tag_condition: Optional[TagCondition] = None,
            offset: float = 0.0,
            volume: float = 0.25,
            interpret_consecutive_words_as_one: bool = True
        ):
        self._sound: Sound = sound
        self._when: EventType = when
        self._what: ElementType = what
        self._tag_condition: Optional[TagCondition] = tag_condition
        self._offset: float = offset
        self._volume: float = volume
        self._interpret_consecutive_words_as_one: bool = interpret_consecutive_words_as_one

    def run(self, document: Document) -> None:
        from movielite import AudioClip

        times = self._get_elements_times(document)
        for time in times:
            path = self._sound.get_file_path()
            time = time.start + self._offset if self._when == EventType.ON_NARRATION_STARTS else time.end + self._offset
            audio = AudioClip(path, start=time, volume=self._volume)
            document.sfxs.append(audio)

    def _get_elements_times(self, document: Document) -> List[TimeFragment]:
        elements = self._get_elements(document)
        elements = self._filter_elements_by_tag(elements)
        return [element.time for element in elements]

    def _get_elements(self, document: Document) -> List[Union[Word, Line, Segment]]:
        match self._what:
            case ElementType.WORD:
                return document.get_words()
            case ElementType.LINE:
                return document.get_lines()
            case ElementType.SEGMENT:
                return document.segments
            case _:
                raise ValueError(f"Unsupported element type: {self._what}")
            
    def _filter_elements_by_tag(self, elements: List[Union[Word, Line, Segment]]) -> List[Union[Word, Line, Segment]]:
        if self._tag_condition is None:
            return elements
        if self._what != ElementType.WORD or not self._interpret_consecutive_words_as_one:
            return [element for element in elements if self._tag_condition.evaluate(element.get_tags())]
        
        filtered_words = []
        consecutive_matched_words = []
        for word in elements:
            if self._tag_condition.evaluate(word.get_tags()):
                consecutive_matched_words.append(word)
            else:
                self._append_proper_word_from_consecutive_words(filtered_words, consecutive_matched_words)
                consecutive_matched_words = []

        self._append_proper_word_from_consecutive_words(filtered_words, consecutive_matched_words)
        return filtered_words
    
    def _append_proper_word_from_consecutive_words(self, words_accumulator: List[Word], consecutive_words: List[Word]) -> None:
        if len(consecutive_words) > 0:
            words_accumulator.append(consecutive_words[0] if self._when == EventType.ON_NARRATION_STARTS else consecutive_words[-1])
        return words_accumulator
