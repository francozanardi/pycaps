import unittest
from unittest.mock import MagicMock, patch

from pycaps.common import ElementState, Line, Segment, TimeFragment, Word
from pycaps.renderer.pictex_subtitle_renderer import PictexSubtitleRenderer


class FakeImage:
    def __init__(self, width: int = 100, height: int = 50):
        self.width = width
        self.height = height

    def to_pillow(self):
        return MagicMock()


class TestPictexSubtitleRenderer(unittest.TestCase):
    def setUp(self):
        self.tf = TimeFragment(start=0.0, end=1.0)
        self.segment = Segment(time=self.tf)
        self.line = Line(time=self.tf)
        self.segment.lines.add(self.line)
        self.word = Word(text="Hello", time=self.tf)
        self.line.words.add(self.word)

    def test_get_word_size_without_padding(self):
        renderer = PictexSubtitleRenderer()
        renderer.open(1280, 1280)

        with patch("pictex.Canvas.render", return_value=FakeImage(100, 50)):
            size = renderer.get_word_size(
                self.word, ElementState.LINE_BEING_NARRATED, ElementState.WORD_NOT_NARRATED_YET
            )
        self.assertEqual(size, (100, 50))

    def test_get_word_size_with_padding(self):
        renderer = PictexSubtitleRenderer()
        renderer.append_css(".word { padding-left: 10px; padding-right: 15px; }")
        renderer.open(1280, 1280)

        with patch("pictex.Canvas.render", return_value=FakeImage(100, 50)):
            size = renderer.get_word_size(
                self.word, ElementState.LINE_BEING_NARRATED, ElementState.WORD_NOT_NARRATED_YET
            )

        # scale_factor = 2.0 at 1280 height
        # extra padding = (10 + 15) * 2.0 = 50
        self.assertEqual(size, (150, 50))

    def test_get_word_size_with_padding_and_borders(self):
        renderer = PictexSubtitleRenderer()
        renderer.append_css(".word { padding-left: 10px; padding-right: 15px; border-width: 2px; }")
        renderer.open(1280, 1280)

        with patch("pictex.Canvas.render", return_value=FakeImage(100, 50)):
            size = renderer.get_word_size(
                self.word, ElementState.LINE_BEING_NARRATED, ElementState.WORD_NOT_NARRATED_YET
            )

        # scale_factor = 2.0 at 1280 height
        # extra = (10 + 15 + 2 + 2) * 2.0 = 58
        self.assertEqual(size, (158, 50))

    def test_get_word_size_caching(self):
        renderer = PictexSubtitleRenderer()
        renderer.open(1280, 1280)

        with patch("pictex.Canvas.render", return_value=FakeImage(100, 50)) as mock_render:
            size1 = renderer.get_word_size(
                self.word, ElementState.LINE_BEING_NARRATED, ElementState.WORD_NOT_NARRATED_YET
            )
            size2 = renderer.get_word_size(
                self.word, ElementState.LINE_BEING_NARRATED, ElementState.WORD_NOT_NARRATED_YET
            )
            self.assertEqual(size1, size2)
            self.assertEqual(mock_render.call_count, 1)

    def test_get_word_size_end_to_end(self):
        renderer = PictexSubtitleRenderer()
        renderer.open(1280, 1280)
        size = renderer.get_word_size(
            self.word, ElementState.LINE_BEING_NARRATED, ElementState.WORD_NOT_NARRATED_YET
        )
        self.assertGreater(size[0], 0)
        self.assertGreater(size[1], 0)

    def test_get_word_padding_width_no_span(self):
        renderer = PictexSubtitleRenderer()
        renderer.open(1280, 1280)
        dummy_node = MagicMock()
        dummy_node.tag = "div"
        dummy_node.children = []
        padding = renderer._get_word_padding_width(dummy_node)
        self.assertEqual(padding, 0)
