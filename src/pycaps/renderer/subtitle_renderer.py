from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple, TYPE_CHECKING
from pycaps.common import Word, ElementState, Line, CacheStrategy

if TYPE_CHECKING:
    from PIL.Image import Image

class SubtitleRenderer(ABC):
    @property
    def custom_css(self) -> str:
        return getattr(self, "_custom_css", "")

    @custom_css.setter
    def custom_css(self, value: str):
        self._custom_css = value

    @abstractmethod
    def append_css(self, css: str):
        pass

    @abstractmethod
    def open(self, video_width: int, video_height: int, resources_dir: Optional[Path] = None, cache_strategy: CacheStrategy = CacheStrategy.CSS_CLASSES_AWARE):
        pass

    @abstractmethod
    def open_line(self, line: Line, line_state: ElementState):
        pass
   
    @abstractmethod   
    def render_word(self, index: int, word: Word, state: ElementState, first_n_letters: Optional[int] = None) -> Optional['Image']:
        pass
    
    @abstractmethod
    def close_line(self):
        pass
 
    @abstractmethod
    def get_word_size(self, word: Word, line_state: ElementState, word_state: ElementState) -> Tuple[int, int]:
        pass

    @abstractmethod
    def close(self):
        pass
