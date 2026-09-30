from .base_transcriber import AudioTranscriber
from .whisper_document_builder import build_document, WhisperSegment, WhisperWord
from typing import Optional, Any
from pycaps.common import Document
from pycaps.logger import logger

class WhisperAudioTranscriber(AudioTranscriber):
    def __init__(self, model_size: str = "base", language: Optional[str] = None, model: Optional[Any] = None, initial_prompt: Optional[str] = None):
        """
        Transcribes audio using OpenAI's Whisper model.

        Args:
            model_size: Size of the Whisper model to use (e.g., "tiny", "base").
            language: Language of the audio (e.g., "en", "es").
            model: (Optional) A pre-loaded Whisper model instance. If provided, model_size is ignored.
            initial_prompt: (Optional) Vocabulary hints for Whisper to improve accuracy on specific words (e.g., brand names).
        """
        self._model_size = model_size
        self._language = language
        self._model = model
        self._initial_prompt = initial_prompt

    def transcribe(self, audio_path: str) -> Document:
        """
        Transcribes the audio file and returns segments with timestamps.
        """
        result = self._get_model().transcribe(
            audio_path,
            word_timestamps=True,
            language=self._language,
            initial_prompt=self._initial_prompt,
            verbose=False # TODO: we should pass our --verbose param here
        )

        if "segments" not in result or not result["segments"]:
            logger().warning("Whisper returned no segments in the transcription.")
            return Document()

        logger().debug(f"Whisper result: {result}")
        return build_document(self._to_whisper_segment(segment_info) for segment_info in result["segments"])

    def _to_whisper_segment(self, segment_info: dict) -> WhisperSegment:
        words = None
        if "words" in segment_info and isinstance(segment_info["words"], list):
            words = [WhisperWord(text=w["word"], start=w["start"], end=w["end"]) for w in segment_info["words"]]
        return WhisperSegment(text=segment_info.get("text", ""), start=segment_info["start"], end=segment_info["end"], words=words)

    def _get_model(self):
        if self._model:
            return self._model
        
        import whisper

        try:
            self._model = whisper.load_model(self._model_size)
            return self._model
        except Exception as e:
            raise RuntimeError(
                f"Error loading Whisper model (size: {self._model_size}): {e}\n" 
                f"Ensure Whisper is installed and models are available (or can be downloaded)."
            )