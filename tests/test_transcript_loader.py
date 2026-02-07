import os
import tempfile
import unittest

from pycaps.transcriber import TranscriptFormat, load_transcription


class TranscriptLoaderTests(unittest.TestCase):
    def test_load_whisper_json_with_word_timestamps(self):
        data = {
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.0,
                    "words": [
                        {"word": "Hello", "start": 0.0, "end": 0.5},
                        {"word": "world", "start": 0.5, "end": 1.0},
                    ],
                }
            ]
        }

        document = load_transcription(data, TranscriptFormat.WHISPER_JSON)
        self.assertEqual(len(document.segments), 1)
        self.assertEqual([word.text for word in document.get_words()], ["Hello", "world"])
        self.assertAlmostEqual(document.get_words()[0].time.start, 0.0)
        self.assertAlmostEqual(document.get_words()[1].time.end, 1.0)

    def test_load_pycaps_document_json_shape(self):
        data = {
            "segments": [
                {
                    "lines": [
                        {
                            "words": [
                                {"text": "Hello", "time": {"start": 0.0, "end": 0.4}},
                                {"text": "there", "time": {"start": 0.4, "end": 0.8}},
                            ]
                        }
                    ]
                }
            ]
        }

        document = load_transcription(data, TranscriptFormat.PYCAPS_JSON)
        self.assertEqual([word.text for word in document.get_words()], ["Hello", "there"])
        self.assertEqual(len(document.segments[0].lines), 1)

    def test_load_pycaps_lightweight_json_shape(self):
        data = {
            "segments": [
                {
                    "words": [
                        {"text": "One", "start": 1.0, "end": 1.5},
                        {"word": "two", "start": 1.5, "end": 2.0},
                    ]
                }
            ]
        }

        document = load_transcription(data, TranscriptFormat.PYCAPS_JSON)
        self.assertEqual([word.text for word in document.get_words()], ["One", "two"])
        self.assertAlmostEqual(document.get_words()[0].time.start, 1.0)
        self.assertAlmostEqual(document.get_words()[1].time.end, 2.0)

    def test_parse_srt_single_word_preserves_cue_timing(self):
        srt = "1\n00:00:01,000 --> 00:00:02,000\nHello\n"
        path = self._write_temp_file(".srt", srt)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))

        document = load_transcription(path, TranscriptFormat.AUTO)
        word = document.get_words()[0]
        self.assertEqual(word.text, "Hello")
        self.assertAlmostEqual(word.time.start, 1.0)
        self.assertAlmostEqual(word.time.end, 2.0)

    def test_parse_srt_multi_word_uses_monotonic_distribution(self):
        srt = "1\n00:00:00,000 --> 00:00:02,000\nHi there friend\n"
        path = self._write_temp_file(".srt", srt)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))

        document = load_transcription(path, TranscriptFormat.SRT)
        words = document.get_words()
        self.assertEqual([word.text for word in words], ["Hi", "there", "friend"])
        self.assertAlmostEqual(words[0].time.start, 0.0)
        self.assertAlmostEqual(words[-1].time.end, 2.0)
        self.assertLess(words[0].time.end, words[1].time.end)
        self.assertLess(words[1].time.end, words[2].time.end)

    def test_parse_vtt_with_inline_timestamp_tags(self):
        vtt = (
            "WEBVTT\n\n"
            "00:00:00.000 --> 00:00:02.000\n"
            "<00:00:00.200>Hello <00:00:01.200>world\n"
        )
        path = self._write_temp_file(".vtt", vtt)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))

        document = load_transcription(path, TranscriptFormat.VTT)
        words = document.get_words()
        self.assertEqual([word.text for word in words], ["Hello", "world"])
        self.assertAlmostEqual(words[0].time.start, 0.2, places=3)
        self.assertAlmostEqual(words[1].time.start, 1.2, places=3)
        self.assertAlmostEqual(words[1].time.end, 2.0, places=3)

    def test_auto_detects_whisper_json_structure(self):
        data = {
            "language": "en",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 1.0,
                    "words": [{"word": "test", "start": 0.0, "end": 1.0}],
                }
            ],
        }

        document = load_transcription(data, TranscriptFormat.AUTO)
        self.assertEqual([word.text for word in document.get_words()], ["test"])

    def test_invalid_format_raises_clear_error(self):
        with self.assertRaisesRegex(ValueError, "Invalid transcript format"):
            load_transcription({"segments": []}, "invalid")

    def _write_temp_file(self, suffix: str, content: str) -> str:
        with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False) as temp:
            temp.write(content)
            return temp.name


if __name__ == "__main__":
    unittest.main()
