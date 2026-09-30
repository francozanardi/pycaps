import json
import os
import sys
import tempfile
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import numpy as np
from typer.testing import CliRunner

from pycaps.cli.cli import app
from pycaps.common import Document
from pycaps.pipeline import CapsPipelineBuilder, JsonConfigLoader
from pycaps.transcriber import FasterWhisperAudioTranscriber, WhisperAudioTranscriber, WhisperBackend

# (text, start, end, words), where words is None or a list of (text, start, end)
SEGMENTS = [
    ("Hello world", 0.0, 1.0, [(" Hello", 0.0, 0.5), (" world", 0.5, 0.5), ("  ", 0.6, 0.7)]),
    ("No words", 1.0, 2.0, None),
    ("Bye", 2.0, 2.0, [(" Bye", 2.0, 2.4)]),
]
EXPECTED_WORDS = [("Hello", 0.0, 0.5), ("world", 0.5, 0.51), ("Bye", 2.0, 2.4)]


class _FakeOpenAiWhisperModel:
    def transcribe(self, *_args, **_kwargs):
        return {"segments": [
            {
                "text": text, "start": start, "end": end,
                **({"words": [{"word": w, "start": s, "end": e} for w, s, e in words]} if words is not None else {}),
            }
            for text, start, end, words in SEGMENTS
        ]}


class _FakeFasterWhisperModel:
    def __init__(self, *_args, device="auto", **_kwargs):
        self.device = device
        self.transcribe_calls = []

    def transcribe(self, audio, **kwargs):
        self.transcribe_calls.append((audio, kwargs))
        segments = (
            SimpleNamespace(
                text=text, start=start, end=end,
                words=[SimpleNamespace(word=w, start=s, end=e) for w, s, e in words] if words is not None else None,
            )
            for text, start, end, words in SEGMENTS
        )
        return segments, SimpleNamespace(language="en")


class _FakeFasterWhisperModelWithoutCuda(_FakeFasterWhisperModel):
    def transcribe(self, audio, **kwargs):
        if self.device != "cpu":
            raise RuntimeError("Library cublas64_12.dll is not found or cannot be loaded")
        return super().transcribe(audio, **kwargs)


def _fake_faster_whisper_module(model_class) -> ModuleType:
    module = ModuleType("faster_whisper")
    module.created_models = []

    def create_model(*args, **kwargs):
        model = model_class(*args, **kwargs)
        module.created_models.append(model)
        return model

    module.WhisperModel = create_model
    return module


def _get_words(document: Document):
    return [(w.text, w.time.start, round(w.time.end, 2)) for w in document.get_words()]


@patch.object(FasterWhisperAudioTranscriber, "_load_audio", return_value=np.zeros(16000, dtype=np.float32))
class WhisperTranscribersTests(unittest.TestCase):

    def test_openai_whisper_builds_document(self, _mock_load_audio):
        document = WhisperAudioTranscriber(model=_FakeOpenAiWhisperModel()).transcribe("audio.wav")

        self.assertEqual(len(document.segments), 2)
        self.assertEqual(_get_words(document), EXPECTED_WORDS)

    def test_faster_whisper_builds_same_document_as_openai_whisper(self, _mock_load_audio):
        model = _FakeFasterWhisperModel()
        document = FasterWhisperAudioTranscriber(model=model, language="en", initial_prompt="Hello").transcribe("audio.wav")

        self.assertEqual(len(document.segments), 2)
        self.assertEqual(_get_words(document), EXPECTED_WORDS)
        _, kwargs = model.transcribe_calls[0]
        self.assertEqual(kwargs, {"word_timestamps": True, "language": "en", "initial_prompt": "Hello"})

    def test_faster_whisper_falls_back_to_cpu_when_cuda_is_not_available(self, _mock_load_audio):
        fake_module = _fake_faster_whisper_module(_FakeFasterWhisperModelWithoutCuda)
        with patch.dict(sys.modules, {"faster_whisper": fake_module}):
            document = FasterWhisperAudioTranscriber().transcribe("audio.wav")

        self.assertEqual([m.device for m in fake_module.created_models], ["auto", "cpu"])
        self.assertEqual(_get_words(document), EXPECTED_WORDS)

    def test_faster_whisper_does_not_fall_back_when_device_is_explicit(self, _mock_load_audio):
        fake_module = _fake_faster_whisper_module(_FakeFasterWhisperModelWithoutCuda)
        with patch.dict(sys.modules, {"faster_whisper": fake_module}):
            with self.assertRaises(RuntimeError):
                FasterWhisperAudioTranscriber(device="cuda").transcribe("audio.wav")

        self.assertEqual(len(fake_module.created_models), 1)


@patch("pycaps.pipeline.caps_pipeline.check_dependencies", return_value=None)
class WhisperBackendConfigTests(unittest.TestCase):

    def test_builder_uses_openai_whisper_by_default(self, _mock_dependencies):
        builder = CapsPipelineBuilder().with_whisper_config(model_size="tiny")
        self.assertIsInstance(builder._caps_pipeline._transcriber, WhisperAudioTranscriber)

    def test_builder_uses_faster_whisper_backend(self, _mock_dependencies):
        builder = CapsPipelineBuilder().with_whisper_config(model_size="tiny", language="es", backend=WhisperBackend.FASTER)
        transcriber = builder._caps_pipeline._transcriber
        self.assertIsInstance(transcriber, FasterWhisperAudioTranscriber)
        self.assertEqual(transcriber._model_size, "tiny")
        self.assertEqual(transcriber._language, "es")

    def test_json_config_uses_faster_whisper_backend(self, _mock_dependencies):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = os.path.join(tmp_dir, "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump({"whisper": {"model": "tiny", "backend": "faster"}}, f)
            builder = JsonConfigLoader(config_path).load(False)

        self.assertIsInstance(builder._caps_pipeline._transcriber, FasterWhisperAudioTranscriber)


class _FakeBuilder:
    whisper_config_calls = []

    def with_whisper_config(self, **kwargs):
        self.__class__.whisper_config_calls.append(kwargs)
        return self

    def build(self, *_args, **_kwargs):
        return SimpleNamespace(run=lambda: None)


class _FakeTemplateLoader:
    def __init__(self, _template):
        pass

    def with_input_video(self, _input_video):
        return self

    def load(self, _should_build_pipeline):
        return _FakeBuilder()


class RenderCliWhisperBackendTests(unittest.TestCase):
    def setUp(self):
        _FakeBuilder.whisper_config_calls = []

    def _render(self, *extra_args):
        with patch("pycaps.cli.render_cli.TemplateFactory"), patch("pycaps.cli.render_cli.TemplateLoader", _FakeTemplateLoader):
            result = CliRunner().invoke(app, ["render", "--input", "video.mp4", "--template", "default", *extra_args])
        self.assertEqual(result.exit_code, 0, result.output)

    def test_whisper_backend_flag_is_forwarded(self):
        self._render("--whisper-backend", "faster", "--whisper-model", "tiny")
        self.assertEqual(_FakeBuilder.whisper_config_calls, [
            {"language": None, "model_size": "tiny", "initial_prompt": None, "backend": WhisperBackend.FASTER},
        ])

    def test_whisper_config_uses_openai_backend_when_flag_is_missing(self):
        self._render("--lang", "es")
        self.assertEqual(_FakeBuilder.whisper_config_calls[0]["backend"], WhisperBackend.OPENAI)


if __name__ == "__main__":
    unittest.main()
