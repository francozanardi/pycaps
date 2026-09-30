from .base_transcriber import AudioTranscriber
from .whisper_document_builder import build_document, WhisperSegment, WhisperWord
from typing import Optional, Any, TYPE_CHECKING
from pycaps.common import Document
from pycaps.logger import logger
import subprocess

if TYPE_CHECKING:
    import numpy as np

# faster-whisper expects the audio as 16kHz mono
SAMPLE_RATE = 16000
GPU_ERROR_KEYWORDS = ("cuda", "cublas", "cudnn")

class FasterWhisperAudioTranscriber(AudioTranscriber):
    def __init__(
            self,
            model_size: str = "base",
            language: Optional[str] = None,
            model: Optional[Any] = None,
            initial_prompt: Optional[str] = None,
            device: str = "auto",
            compute_type: str = "default",
        ):
        """
        Transcribes audio using faster-whisper, a reimplementation of Whisper using CTranslate2.
        It's faster and uses less memory than openai-whisper, especially on CPU.

        Args:
            model_size: Size of the Whisper model to use (e.g., "tiny", "base").
            language: Language of the audio (e.g., "en", "es").
            model: (Optional) A pre-loaded faster_whisper.WhisperModel instance. If provided, model_size, device and compute_type are ignored.
            initial_prompt: (Optional) Vocabulary hints for Whisper to improve accuracy on specific words (e.g., brand names).
            device: Device to run the model on ("auto", "cpu" or "cuda").
            compute_type: Quantization type used by the model (e.g., "default", "int8", "float16").
        """
        self._model_size = model_size
        self._language = language
        self._model = model
        self._is_model_provided = model is not None
        self._initial_prompt = initial_prompt
        self._device = device
        self._compute_type = compute_type

    def transcribe(self, audio_path: str) -> Document:
        """
        Transcribes the audio file and returns segments with timestamps.
        """
        audio = self._load_audio(audio_path)
        try:
            return self._transcribe(audio)
        except RuntimeError as e:
            if not self._should_fallback_to_cpu(e):
                raise
            logger().warning(f"faster-whisper couldn't run on GPU ({e}). Falling back to CPU.")
            self._model = None
            self._device = "cpu"
            return self._transcribe(audio)

    def _transcribe(self, audio: "np.ndarray") -> Document:
        segments, _ = self._get_model().transcribe(
            audio,
            word_timestamps=True,
            language=self._language,
            initial_prompt=self._initial_prompt,
        )
        # segments is a lazy generator: the transcription runs while it's being consumed
        return build_document(self._to_whisper_segment(segment) for segment in segments)

    def _should_fallback_to_cpu(self, error: RuntimeError) -> bool:
        """
        With device "auto", CTranslate2 picks CUDA whenever there is a GPU, even if the CUDA libraries are missing.
        In that case, it fails only when the transcription starts.
        """
        if self._device != "auto" or self._is_model_provided:
            return False
        message = str(error).lower()
        return any(keyword in message for keyword in GPU_ERROR_KEYWORDS)

    def _load_audio(self, audio_path: str) -> "np.ndarray":
        """
        Decodes the audio with ffmpeg instead of letting faster-whisper do it,
        since faster-whisper uses PyAV, and some of its versions are not compatible with the latest PyAV.
        """
        import numpy as np

        cmd = [
            "ffmpeg", "-nostdin", "-i", audio_path,
            "-f", "s16le", "-ac", "1", "-acodec", "pcm_s16le", "-ar", str(SAMPLE_RATE),
            "-loglevel", "error", "-",
        ]
        try:
            output = subprocess.run(cmd, capture_output=True, check=True).stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Unable to decode audio file {audio_path}: {e.stderr.decode(errors='ignore')}")

        return np.frombuffer(output, np.int16).astype(np.float32) / 32768.0

    def _to_whisper_segment(self, segment: Any) -> WhisperSegment:
        words = None
        if segment.words is not None:
            words = [WhisperWord(text=w.word, start=w.start, end=w.end) for w in segment.words]
        return WhisperSegment(text=segment.text, start=segment.start, end=segment.end, words=words)

    def _get_model(self):
        if self._model:
            return self._model

        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise RuntimeError(
                "faster-whisper is not installed. Install it with: pip install faster-whisper"
            )

        try:
            self._model = WhisperModel(self._model_size, device=self._device, compute_type=self._compute_type)
            return self._model
        except Exception as e:
            raise RuntimeError(
                f"Error loading faster-whisper model (size: {self._model_size}): {e}\n"
                f"Ensure the model is available (or can be downloaded)."
            )
