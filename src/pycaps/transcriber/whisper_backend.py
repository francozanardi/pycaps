from enum import Enum

class WhisperBackend(str, Enum):
    OPENAI = "openai"
    FASTER = "faster"
