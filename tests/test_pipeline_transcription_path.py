import unittest
from unittest.mock import MagicMock, patch

from pycaps.common import Document, Line, Segment, TimeFragment, Word
from pycaps.pipeline.caps_pipeline import CapsPipeline


def _make_document(text: str, start: float = 0.0, end: float = 1.0) -> Document:
    document = Document()
    segment_time = TimeFragment(start=start, end=end)
    segment = Segment(time=segment_time)
    line = Line(time=segment_time)
    line.words.add(Word(text=text, time=TimeFragment(start=start, end=end)))
    segment.lines.add(line)
    document.segments.add(segment)
    return document


class PipelineTranscriptionPathTests(unittest.TestCase):
    @patch("pycaps.pipeline.caps_pipeline.check_dependencies", return_value=None)
    def test_external_transcription_skips_built_in_transcribe(self, _mock_dependencies):
        pipeline = CapsPipeline()
        external_document = _make_document("external")
        processed_document = _make_document("processed")

        pipeline.prepare = MagicMock()
        pipeline.transcribe = MagicMock()
        pipeline.process_document = MagicMock(return_value=processed_document)
        pipeline.render = MagicMock()
        pipeline._transcription_for_loading = external_document

        pipeline.run()

        pipeline.transcribe.assert_not_called()
        pipeline.process_document.assert_called_once_with(external_document)
        pipeline.render.assert_called_once_with(processed_document)

    @patch("pycaps.pipeline.caps_pipeline.check_dependencies", return_value=None)
    def test_subtitle_data_path_still_skips_transcribe_and_processing(self, _mock_dependencies):
        pipeline = CapsPipeline()
        loaded_document = _make_document("loaded")

        pipeline.prepare = MagicMock()
        pipeline.transcribe = MagicMock()
        pipeline.process_document = MagicMock()
        pipeline.render = MagicMock()
        pipeline._subtitle_data_path_for_loading = "subtitle_data.json"

        with patch("pycaps.pipeline.caps_pipeline.SubtitleDataService") as subtitle_data_service:
            subtitle_data_service.return_value.load.return_value = loaded_document
            pipeline.run()

        subtitle_data_service.assert_called_once_with("subtitle_data.json")
        pipeline.transcribe.assert_not_called()
        pipeline.process_document.assert_not_called()
        pipeline.render.assert_called_once_with(loaded_document)

    @patch("pycaps.pipeline.caps_pipeline.check_dependencies", return_value=None)
    def test_default_flow_still_transcribes_and_processes(self, _mock_dependencies):
        pipeline = CapsPipeline()
        transcribed_document = _make_document("transcribed")
        processed_document = _make_document("processed")

        pipeline.prepare = MagicMock()
        pipeline.transcribe = MagicMock(return_value=transcribed_document)
        pipeline.process_document = MagicMock(return_value=processed_document)
        pipeline.render = MagicMock()

        pipeline.run()

        pipeline.transcribe.assert_called_once()
        pipeline.process_document.assert_called_once_with(transcribed_document)
        pipeline.render.assert_called_once_with(processed_document)


if __name__ == "__main__":
    unittest.main()
