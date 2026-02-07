import unittest
from unittest.mock import patch

from typer.testing import CliRunner

from pycaps.cli.cli import app


class _FakePipeline:
    ran = False

    def run(self):
        _FakePipeline.ran = True


class _FakeBuilder:
    transcript_calls = []
    subtitle_data_calls = []
    build_calls = 0

    @classmethod
    def reset(cls):
        cls.transcript_calls = []
        cls.subtitle_data_calls = []
        cls.build_calls = 0
        _FakePipeline.ran = False

    def with_output_video(self, *_args, **_kwargs):
        return self

    def add_css_content(self, *_args, **_kwargs):
        return self

    def with_whisper_config(self, *_args, **_kwargs):
        return self

    def with_subtitle_data_path(self, path):
        self.__class__.subtitle_data_calls.append(path)
        return self

    def with_transcription_file(self, path, format):
        self.__class__.transcript_calls.append((path, format))
        return self

    def should_preview_transcription(self, *_args, **_kwargs):
        return self

    def with_video_quality(self, *_args, **_kwargs):
        return self

    def with_layout_options(self, *_args, **_kwargs):
        return self

    def build(self, *_args, **_kwargs):
        self.__class__.build_calls += 1
        return _FakePipeline()


class _FakeTemplateLoader:
    def __init__(self, _template):
        pass

    def with_input_video(self, _input_video):
        return self

    def load(self, _should_build_pipeline):
        return _FakeBuilder()


class RenderCliTranscriptFlagsTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        _FakeBuilder.reset()

    def test_transcript_flag_is_accepted_and_forwarded(self):
        with patch("pycaps.cli.render_cli.TemplateFactory") as template_factory:
            template_factory.return_value.create.return_value = object()
            with patch("pycaps.cli.render_cli.TemplateLoader", _FakeTemplateLoader):
                result = self.runner.invoke(
                    app,
                    ["render", "--input", "video.mp4", "--template", "default", "--transcript", "transcript.json"],
                )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(len(_FakeBuilder.transcript_calls), 1)
        self.assertEqual(_FakeBuilder.transcript_calls[0][0], "transcript.json")
        self.assertTrue(_FakePipeline.ran)

    def test_transcript_format_requires_transcript(self):
        result = self.runner.invoke(
            app,
            ["render", "--input", "video.mp4", "--template", "default", "--transcript-format", "srt"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("--transcript-format requires --transcript", result.output)

    def test_transcript_and_subtitle_data_are_mutually_exclusive(self):
        result = self.runner.invoke(
            app,
            [
                "render",
                "--input",
                "video.mp4",
                "--template",
                "default",
                "--transcript",
                "transcript.srt",
                "--subtitle-data",
                "already_processed.json",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Only one of --subtitle-data or --transcript can be provided", result.output)


if __name__ == "__main__":
    unittest.main()
