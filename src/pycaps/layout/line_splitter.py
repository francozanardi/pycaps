from typing import List
from .definitions import SubtitleLayoutOptions, TextOverflowStrategy
from pycaps.common import Document, Line, Word, TimeFragment, Segment

class LineSplitter:
    def __init__(self, layout_options: SubtitleLayoutOptions):
        self._options = layout_options

    def split_into_lines(self, document: Document, video_width: int) -> None:
        """
        Splits the segments into lines.
        """
        for segment in document.segments:
            self._split_segment_into_lines(segment, video_width)

    def _split_segment_into_lines(self, segment: Segment, video_width: int) -> None:
        """Splits segments into lines based on layout options."""
        lines: List[Line] = []
        current_line_words: List[Word] = []
        current_line_total_width = 0
        max_w = video_width * self._options.max_width_ratio
        x_words_space = self._options.x_words_space

        for word in segment.get_words():
            word_width = word.max_layout.size.width
            word_width_with_spacing = word_width + x_words_space

            if (len(lines) >= self._options.max_number_of_lines - 1 and 
                self._options.on_text_overflow_strategy == TextOverflowStrategy.EXCEED_MAX_WIDTH_RATIO_IN_LAST_LINE):
                current_line_words.append(word)
                current_line_total_width += x_words_space + word_width
                continue

            if current_line_total_width + word_width_with_spacing <= max_w:
                current_line_words.append(word)
                current_line_total_width += x_words_space + word_width
            else:
                self._append_new_line(lines, current_line_words)
                current_line_words = [word]
                current_line_total_width = word_width
        
        self._append_new_line(lines, current_line_words)
        if len(lines) > 0:
            self._adjust_lines_to_constraints(lines)
        segment.lines.set_all(lines)

    def _adjust_lines_to_constraints(self, lines: List[Line]) -> None:
        """Adjusts lines according to min/max constraints and overflow strategy."""
        # If we have fewer lines than minimum, split the longest line
        while len(lines) < self._options.min_number_of_lines:
            longest_line = max(lines, key=lambda l: l.max_layout.size.width)
            number_of_words = len(longest_line.words)
            if number_of_words <= 1:
                break
            mid_point = number_of_words // 2
            
            first_half = longest_line.words[:mid_point]
            second_half = longest_line.words[mid_point:]
            
            first_line = Line(time=TimeFragment(start=first_half[0].time.start, end=first_half[-1].time.end))
            second_line = Line(time=TimeFragment(start=second_half[0].time.start, end=second_half[-1].time.end))

            first_line.words.set_all(first_half)
            second_line.words.set_all(second_half)

            to_remove = lines.index(longest_line)
            lines[to_remove:to_remove+1] = [first_line, second_line] # replace the longest line with the two new ones
        
    def _append_new_line(self, lines: List[Line], words: List[Word]) -> None:
        if not words:
            return
        time = TimeFragment(start=words[0].time.start, end=words[-1].time.end)
        line = Line(time=time)
        line.words.set_all(words)
        lines.append(line)
