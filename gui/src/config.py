import os
import tempfile

MAX_CONCURRENT_JOBS = 3
LOCK_DIR = os.path.join(tempfile.gettempdir(), "pycaps_locks")
os.makedirs(LOCK_DIR, exist_ok=True)
MAX_VIDEO_SIZE = 50 * 1024 * 1024
LOCK_TTL_SECONDS = 20 * 60
SESSION_TTL_SECONDS = 60 * 60
MAX_VIDEO_DURATION = 60

TEMPLATES_INFO = [
    {"name": "classic", "ai_features": []},
    {"name": "fast", "ai_features": []},
    {"name": "word-focus", "ai_features": []},
    {"name": "line-focus", "ai_features": []},
    {"name": "minimalist", "ai_features": []},
    {"name": "neo-minimal", "ai_features": ["AI Tagger"]},
    {"name": "hype", "ai_features": ["Auto-Emoji"]},
    {"name": "retro-gaming", "ai_features": []},
    {"name": "vibrant", "ai_features": []},
    {"name": "explosive", "ai_features": []},
]
TEMPLATE_NAMES = [t["name"] for t in TEMPLATES_INFO]

SUPPORTED_LANGUAGES = {   
    "Italian": ("it-IT", "it"),
    "English (US)": ("en-US", "en"),
    "Spanish": ("es-ES", "es"),
    "French": ("fr-FR", "fr"),
    "German": ("de-DE", "de"),
    "Portuguese": ("pt-BR", "pt"),
    "Dutch": ("nl-NL", "nl"),
    "Russian": ("ru-RU", "ru"),
    "Japanese": ("ja-JP", "ja"),
    "Korean": ("ko-KR", "ko"),
    "Chinese (Mandarin)": ("cmn-CN", "zh"),
    "Hindi": ("hi-IN", "hi"),
    "Arabic": ("ar-SA", "ar"),
}
