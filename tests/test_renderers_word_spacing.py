import importlib.util
import os
import tempfile
import unittest
from typing import Callable, Dict, Tuple
from unittest.mock import patch

from pycaps.common import Document, ElementState, Line, Segment, TimeFragment, Word
from pycaps.pipeline import CapsPipelineBuilder
from pycaps.renderer import CssSubtitleRenderer, PictexSubtitleRenderer
from pycaps.template import TemplateFactory

VIDEO_SIZE = (1080, 1920)
WORDS = ["like", "my", "phone", "went"]
# Keeps the ink measurable: without shadows and backgrounds the alpha channel only covers the glyphs.
# text-transform is disabled because html2pic does not support it, and we want the same glyphs in both renderers.
MEASUREMENT_CSS = ".word { text-shadow: none; text-transform: none; } .word-being-narrated { background-color: transparent; }"
# Every word has a clip for this state, so it's the one we measure
MEASURED_STATES = [ElementState.LINE_BEING_NARRATED, ElementState.WORD_BEING_NARRATED]
# Tolerance for the glyph side bearings, which are not identical between Chromium and Skia.
MAX_GAP_DIFFERENCE_PX = 6

WordPair = Tuple[str, str]


def _make_document() -> Document:
    document = Document()
    segment_time = TimeFragment(start=0.0, end=float(len(WORDS)))
    segment = Segment(time=segment_time)
    line = Line(time=segment_time)
    for i, text in enumerate(WORDS):
        line.words.add(Word(text=text, time=TimeFragment(start=float(i), end=float(i + 1))))
    segment.lines.add(line)
    document.segments.add(segment)
    return document


def _get_gaps_between_words(document: Document) -> Dict[WordPair, int]:
    """
    Returns the visible distance, in pixels, between the ink of each pair of consecutive words in a line.
    """
    gaps: Dict[WordPair, int] = {}
    for line in document.get_lines():
        ink_bounds = []
        for word in line.words:
            clip = next(c for c in word.clips if c.states == MEASURED_STATES)
            alpha = clip.media_clip.get_frame(0)[:, :, 3]
            ink_columns = alpha.any(axis=0).nonzero()[0]
            x = clip.layout.position.x
            ink_bounds.append((word.text, x + ink_columns[0], x + ink_columns[-1] + 1))

        for (left_text, _, left_end), (right_text, right_start, _) in zip(ink_bounds, ink_bounds[1:]):
            gaps[(left_text, right_text)] = right_start - left_end
    return gaps


# Video generation is mocked, so ffmpeg is not required
@patch("pycaps.pipeline.caps_pipeline.check_dependencies", return_value=None)
def _render_and_get_gaps(configure_builder: Callable[[CapsPipelineBuilder, str], None], _mock_dependencies) -> Dict[WordPair, int]:
    template = TemplateFactory().create("word-focus")
    template_folder = template.get_folder_path()
    css_path = os.path.join(template_folder, "styles.css")

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_video = os.path.join(tmp_dir, "input.mp4")
        open(input_video, "wb").close()

        builder = CapsPipelineBuilder()
        builder.with_input_video(input_video)
        builder.with_resources(os.path.join(template_folder, "resources"))
        builder.with_transcription(_make_document())
        builder.should_save_subtitle_data(False)
        configure_builder(builder, css_path)
        builder.add_css_content(MEASUREMENT_CSS)
        pipeline = builder.build()

        rendered_documents = []
        with patch("pycaps.video.video_generator.VideoGenerator.start"), \
             patch("pycaps.video.video_generator.VideoGenerator.get_sanitized_fragment_time", return_value=None), \
             patch("pycaps.video.video_generator.VideoGenerator.get_video_size", return_value=VIDEO_SIZE), \
             patch("pycaps.video.video_generator.VideoGenerator.generate", side_effect=rendered_documents.append), \
             patch("pycaps.video.video_generator.VideoGenerator.close"), \
             patch("pycaps.api.api_sender.start"), \
             patch("pycaps.api.api_sender.close"):
            pipeline.run()

    return _get_gaps_between_words(rendered_documents[0])


def _use_css_renderer(builder: CapsPipelineBuilder, css_path: str) -> None:
    builder.with_custom_subtitle_renderer(CssSubtitleRenderer())
    builder.add_css(css_path)


def _use_pictex_renderer_before_css(builder: CapsPipelineBuilder, css_path: str) -> None:
    builder.with_custom_subtitle_renderer(PictexSubtitleRenderer())
    builder.add_css(css_path)


def _use_pictex_renderer_after_css(builder: CapsPipelineBuilder, css_path: str) -> None:
    # This is what happens when a template is loaded with TemplateLoader and then the renderer is replaced
    builder.add_css(css_path)
    builder.with_custom_subtitle_renderer(PictexSubtitleRenderer())


@unittest.skipUnless(
    importlib.util.find_spec("playwright") and importlib.util.find_spec("html2pic"),
    "Both renderers are required: install playwright (with chromium) and html2pic",
)
class RenderersWordSpacingTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.css_renderer_gaps = _render_and_get_gaps(_use_css_renderer)

    def assert_same_gaps_as_css_renderer(self, gaps: Dict[WordPair, int]) -> None:
        self.assertEqual(set(gaps), set(self.css_renderer_gaps), "Both renderers should split the words into the same lines")
        for pair, css_renderer_gap in self.css_renderer_gaps.items():
            self.assertGreater(css_renderer_gap, MAX_GAP_DIFFERENCE_PX, f"Unexpected gap for {pair} with the css renderer")
            self.assertAlmostEqual(
                gaps[pair], css_renderer_gap, delta=MAX_GAP_DIFFERENCE_PX,
                msg=f"Gap between {pair}: pictex={gaps[pair]}px, css={css_renderer_gap}px",
            )

    def test_pictex_renderer_set_before_css_has_same_word_gaps_as_css_renderer(self):
        self.assert_same_gaps_as_css_renderer(_render_and_get_gaps(_use_pictex_renderer_before_css))

    def test_pictex_renderer_set_after_css_has_same_word_gaps_as_css_renderer(self):
        self.assert_same_gaps_as_css_renderer(_render_and_get_gaps(_use_pictex_renderer_after_css))


if __name__ == "__main__":
    unittest.main()
