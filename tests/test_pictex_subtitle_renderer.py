import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pycaps.common import Document, Line, Segment, TimeFragment, Word, ElementState, CacheStrategy
from pycaps.pipeline import CapsPipelineBuilder
from pycaps.renderer import PictexSubtitleRenderer, SubtitleRenderer
from pycaps.template import TemplateLoader, TemplateFactory


def _create_sample_word(text: str = "Test") -> tuple[Segment, Line, Word]:
    seg = Segment()
    line = Line(seg)
    seg.lines.set_all([line])
    word = Word(line, text=text)
    line.words.set_all([word])
    return seg, line, word


class PictexSubtitleRendererTemplateStylesTests(unittest.TestCase):

    def test_pipeline_builder_preserves_template_styles_in_pictex_renderer(self):
        loader = TemplateLoader("classic")
        builder = loader.load(should_build_pipeline=False)
        original_css = builder._caps_pipeline._renderer.custom_css
        self.assertTrue(len(original_css) > 0)
        self.assertIn(".word", original_css)

        pictex = PictexSubtitleRenderer()
        self.assertEqual(pictex.custom_css, "")

        builder.with_custom_subtitle_renderer(pictex)

        self.assertIs(builder._caps_pipeline._renderer, pictex)
        self.assertEqual(pictex.custom_css, original_css)
        self.assertIn(".word", pictex.custom_css)
        self.assertIn("text-shadow", pictex.custom_css)

    def test_template_loader_with_custom_subtitle_renderer_method(self):
        pictex = PictexSubtitleRenderer()
        loader = TemplateLoader("classic").with_custom_subtitle_renderer(pictex)
        builder = loader.load(should_build_pipeline=False)

        self.assertIs(builder._caps_pipeline._renderer, pictex)
        self.assertTrue(len(pictex.custom_css) > 0)
        self.assertIn(".word", pictex.custom_css)
        self.assertIn("text-shadow", pictex.custom_css)

    def test_pictex_from_template_factory_method(self):
        renderer = PictexSubtitleRenderer.from_template("classic")
        self.assertTrue(len(renderer.custom_css) > 0)
        self.assertIn(".word", renderer.custom_css)
        self.assertIn("18px", renderer.custom_css)

    def test_pictex_init_with_template_argument(self):
        renderer = PictexSubtitleRenderer(template="classic")
        self.assertTrue(len(renderer.custom_css) > 0)
        self.assertIn(".word", renderer.custom_css)

    def test_template_loader_preserves_resources_directory(self):
        loader = TemplateLoader("default")
        builder = loader.load(should_build_pipeline=False)
        pictex = PictexSubtitleRenderer()
        builder.with_custom_subtitle_renderer(pictex)

        self.assertIsNotNone(pictex.resources_dir)
        self.assertTrue(pictex.resources_dir.exists())
        self.assertIn("CustomFont", pictex.custom_css)

    def test_custom_styles_dict_passed_to_init(self):
        styles_dict = {
            "word": {"color": "#ff0000", "font-size": "28px"},
            "word-being-narrated": {"color": "#00ff00"}
        }
        renderer = PictexSubtitleRenderer(styles=styles_dict)
        self.assertIn(".word { color: #ff0000; font-size: 28px; }", renderer.custom_css)
        self.assertIn(".word-being-narrated { color: #00ff00; }", renderer.custom_css)

    def test_flat_styles_dict_defaults_to_word_selector(self):
        styles_dict = {"color": "white", "font-size": "24px"}
        renderer = PictexSubtitleRenderer(styles=styles_dict)
        self.assertIn(".word { color: white; font-size: 24px; }", renderer.custom_css)

    def test_custom_styles_override_template_styles(self):
        loader = TemplateLoader("classic")
        builder = loader.load(should_build_pipeline=False)

        custom_styles = {"word": {"font-size": "36px", "color": "yellow"}}
        pictex = PictexSubtitleRenderer(styles=custom_styles)
        builder.with_custom_subtitle_renderer(pictex)

        # Template styles should be prepended and custom styles appended
        self.assertIn("text-shadow", pictex.custom_css)
        self.assertIn("font-size: 36px", pictex.custom_css)
        # Custom style appears after template style
        template_pos = pictex.custom_css.find("18px")
        custom_pos = pictex.custom_css.find("36px")
        self.assertTrue(template_pos < custom_pos)

    def test_pipeline_builder_add_styles_dict(self):
        builder = CapsPipelineBuilder()
        builder.with_custom_subtitle_renderer(PictexSubtitleRenderer())
        builder.add_styles({"word": {"color": "cyan"}})
        self.assertIn(".word { color: cyan; }", builder._caps_pipeline._renderer.custom_css)

    def test_pipeline_builder_add_css_content_dict(self):
        builder = CapsPipelineBuilder()
        builder.with_custom_subtitle_renderer(PictexSubtitleRenderer())
        builder.add_css_content({"word": {"background-color": "black"}})
        self.assertIn(".word { background-color: black; }", builder._caps_pipeline._renderer.custom_css)

    def test_dimensions_and_scale_factor_respects_configuration(self):
        renderer = PictexSubtitleRenderer(video_width=1920, video_height=1080)
        self.assertEqual(renderer.video_width, 1920)
        self.assertEqual(renderer.video_height, 1080)
        self.assertEqual(renderer.video_dimensions, (1920, 1080))
        expected_scale = 2.0 * (1080 / 1280)
        self.assertAlmostEqual(renderer.scale_factor, expected_scale)

        custom_scale_renderer = PictexSubtitleRenderer(scale_factor=3.5)
        self.assertEqual(custom_scale_renderer.scale_factor, 3.5)
        custom_scale_renderer.open(1920, 1080)
        # Custom scale factor remains respected after open
        self.assertEqual(custom_scale_renderer.scale_factor, 3.5)

    def test_pictex_renders_word_with_classic_template_styles(self):
        loader = TemplateLoader("classic")
        builder = loader.load(should_build_pipeline=False)
        renderer = PictexSubtitleRenderer()
        builder.with_custom_subtitle_renderer(renderer)
        renderer.open(1920, 1080)

        seg, line, word = _create_sample_word("Test")
        renderer.open_line(line, ElementState.WORD_BEING_NARRATED)
        image = renderer.render_word(0, word, ElementState.WORD_BEING_NARRATED)
        renderer.close_line()

        self.assertIsNotNone(image)
        width, height = renderer.get_word_size(word, ElementState.WORD_BEING_NARRATED, ElementState.WORD_BEING_NARRATED)
        self.assertEqual(image.size, (width, height))
        self.assertEqual((width, height), (75, 50))

    def test_pictex_renders_word_with_custom_font_size_override(self):
        loader = TemplateLoader("classic")
        builder = loader.load(should_build_pipeline=False)
        renderer = PictexSubtitleRenderer(styles={"word": {"font-size": "36px"}})
        builder.with_custom_subtitle_renderer(renderer)
        renderer.open(1920, 1080)

        seg, line, word = _create_sample_word("Test")
        renderer.open_line(line, ElementState.WORD_BEING_NARRATED)
        image = renderer.render_word(0, word, ElementState.WORD_BEING_NARRATED)
        renderer.close_line()

        self.assertIsNotNone(image)
        width, height = renderer.get_word_size(word, ElementState.WORD_BEING_NARRATED, ElementState.WORD_BEING_NARRATED)
        self.assertEqual(image.size, (width, height))
        # Larger font size results in larger rendered dimensions
        self.assertEqual((width, height), (136, 87))

    def test_hidden_word_display_none_returns_none_and_zero_size(self):
        renderer = PictexSubtitleRenderer(styles={".word-not-narrated-yet": {"display": "none"}})
        renderer.open(1920, 1080)

        seg, line, word = _create_sample_word("Hidden")
        renderer.open_line(line, ElementState.LINE_NOT_NARRATED_YET)
        image = renderer.render_word(0, word, ElementState.WORD_NOT_NARRATED_YET)
        renderer.close_line()

        self.assertIsNone(image)
        size = renderer.get_word_size(word, ElementState.LINE_NOT_NARRATED_YET, ElementState.WORD_NOT_NARRATED_YET)
        self.assertEqual(size, (0, 0))

    def test_working_directory_restored_on_render_failure(self):
        original_cwd = os.getcwd()
        resources_dir = Path("/tmp")
        renderer = PictexSubtitleRenderer(resources_dir=resources_dir)
        renderer.open(1920, 1080)

        seg, line, word = _create_sample_word("Fail")
        renderer.open_line(line, ElementState.WORD_BEING_NARRATED)
        with patch("html2pic.Html2Pic", side_effect=RuntimeError("Simulated failure")):
            image = renderer.render_word(0, word, ElementState.WORD_BEING_NARRATED)

        renderer.close_line()
        self.assertIsNone(image)
        # Working directory must be restored to original
        self.assertEqual(os.getcwd(), original_cwd)

    def test_template_methods_get_css_and_resources_path(self):
        template = TemplateFactory().create("classic")
        css = template.get_css()
        self.assertTrue(len(css) > 0)
        self.assertIn(".word", css)
        self.assertIsNotNone(template.get_css_path())
        self.assertIsNone(template.get_resources_path())

        default_template = TemplateFactory().create("default")
        self.assertIsNotNone(default_template.get_resources_path())


if __name__ == "__main__":
    unittest.main()
