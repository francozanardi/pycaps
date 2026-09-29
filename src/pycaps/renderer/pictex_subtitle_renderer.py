from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple
from ..common import Line, Word, ElementState, CacheStrategy, Tag
from .subtitle_renderer import SubtitleRenderer
from .rendered_image_cache import RenderedImageCache
import os

if TYPE_CHECKING:
    from PIL.Image import Image

class PictexSubtitleRenderer(SubtitleRenderer):

    DEFAULT_CSS_CLASS_FOR_EACH_WORD: str = "word"
    DEFAULT_CSS_CLASS_FOR_EACH_LINE: str = "line"
    BASE_SCALE_FACTOR: float = 2.0
    REFERENCE_VIDEO_HEIGHT: int = 1280
    MIN_SCALE_MODIFIER: float = 0.25
    MAX_SCALE_MODIFIER: float = 5.0
    
    def __init__(self):
        super().__init__()
        self._custom_css: str = ""
        self._current_line: Optional[Line] = None
        self._current_line_state: Optional[ElementState] = None
        self._resources_dir: Optional[Path] = None
        self._original_cwd: Optional[Path] = None
        self._cache_strategy = CacheStrategy.CSS_CLASSES_AWARE
        self._image_cache: RenderedImageCache = None
        self._scale_factor: float = self.BASE_SCALE_FACTOR
        self._word_size_cache: dict[str, Tuple[int, int]] = {}

    def _calculate_scale_modifier(self, video_height: int) -> float:
        """Calculates a scale modifier based on video height relative to reference."""
        modifier = video_height / self.REFERENCE_VIDEO_HEIGHT
        return max(self.MIN_SCALE_MODIFIER, min(self.MAX_SCALE_MODIFIER, modifier))

    def append_css(self, css: str):
        self._custom_css += css

    def open(self, video_width: int, video_height: int, resources_dir: Optional[Path] = None, cache_strategy: CacheStrategy = CacheStrategy.CSS_CLASSES_AWARE):
        scale_modifier = self._calculate_scale_modifier(video_height)
        self._scale_factor = self.BASE_SCALE_FACTOR * scale_modifier
        self._resources_dir = resources_dir
        self._cache_strategy = cache_strategy
        self._image_cache = RenderedImageCache(self._custom_css, self._cache_strategy)
        self._word_size_cache = {}

    def open_line(self, line: Line, line_state: ElementState):
        if self._current_line:
            raise RuntimeError("A line is already open. Call close_line() first.")
        
        self._current_line = line
        self._current_line_state = line_state
   
    def render_word(self, index: int, word: Word, state: ElementState, first_n_letters: Optional[int] = None) -> Optional['Image']:
        from pictex import CropMode
        from html2pic import Html2Pic
        
        if not self._current_line:
            raise RuntimeError("No line is open. Call open_line() first.")
        
        line_css_classes = self.get_line_css_classes(self._current_line.get_segment().get_tags(), self._current_line.get_tags(), self._current_line_state)
        word_css_classes = self.get_word_css_classes(word.get_tags(), index, state)
        all_css_classes = line_css_classes + " " + word_css_classes
        if self._image_cache.has(index, word.text, all_css_classes, first_n_letters):
            return self._image_cache.get(index, word.text, all_css_classes, first_n_letters)

        self._use_resources_dir_as_cwd()
        text = word.text[:first_n_letters] if first_n_letters else word.text
        renderer = Html2Pic(self.get_html(line_css_classes, word_css_classes, text), self._custom_css)
        canvas, root_element = renderer._translator.translate(renderer.styled_tree, renderer.font_registry)
        try:
            image = canvas.render(root_element, crop_mode=CropMode.CONTENT_BOX, scale_factor=self._scale_factor)
            pillow_image = image.to_pillow()
            self._image_cache.set(index, word.text, all_css_classes, first_n_letters, pillow_image)
            self._go_to_original_cwd()
            return pillow_image
        except:
            self._go_to_original_cwd()
            return None

    def close_line(self):
        self._current_line = None
        self._current_line_state = None
 
    def get_word_size(self, word: Word, line_state: ElementState, word_state: ElementState) -> Tuple[int, int]:
        from pictex import CropMode
        from html2pic import Html2Pic
        
        if self._current_line:
            raise RuntimeError("A line process is in progress. Call close_line() first.")

        line_css_classes = self.get_line_css_classes(word.get_segment().get_tags(), word.get_line().get_tags(), line_state)
        word_css_classes = self.get_word_css_classes(word.get_tags(), word_state=word_state)
        all_css_classes = line_css_classes + " " + word_css_classes
        cache_key = f"word:{word.text}|css_classes:{all_css_classes}"
        if self._word_size_cache is not None and cache_key in self._word_size_cache:
            return self._word_size_cache[cache_key]

        self._use_resources_dir_as_cwd()
        renderer = Html2Pic(self.get_html(line_css_classes, word_css_classes, word.text), self._custom_css)
        canvas, root_element = renderer._translator.translate(renderer.styled_tree, renderer.font_registry)
        try: 
            image = canvas.render(root_element, crop_mode=CropMode.CONTENT_BOX, scale_factor=self._scale_factor)
            self._image_cache.set(-1, word.text, all_css_classes, None, image.to_pillow())
            padding_width = self._get_word_padding_width(renderer.styled_tree)
            size = (image.width + padding_width, image.height)
            if self._word_size_cache is not None:
                self._word_size_cache[cache_key] = size
            self._go_to_original_cwd()
            return size
        except:
            self._go_to_original_cwd()
            return (0, 0)

    def _get_word_padding_width(self, styled_tree) -> int:
        def find_span(node):
            if getattr(node, 'tag', None) == 'span':
                return node
            for child in getattr(node, 'children', []):
                found = find_span(child)
                if found:
                    return found
            return None

        span = find_span(styled_tree)
        if not span:
            return 0

        styles = getattr(span, 'computed_styles', {})
        def parse_px(val):
            if isinstance(val, str) and val.endswith('px'):
                try:
                    return float(val[:-2])
                except ValueError:
                    return 0.0
            elif isinstance(val, (int, float)):
                return float(val)
            return 0.0

        pad_left = parse_px(styles.get('padding-left', '0px'))
        pad_right = parse_px(styles.get('padding-right', '0px'))

        border_general = styles.get('border-width', '0px')
        border_left = parse_px(styles.get('border-left-width', border_general))
        border_right = parse_px(styles.get('border-right-width', border_general))

        extra_width = (pad_left + pad_right + border_left + border_right) * self._scale_factor
        return int(extra_width)

    def _use_resources_dir_as_cwd(self):
        if self._resources_dir:
            self._original_cwd = os.getcwd()
            os.chdir(self._resources_dir)

    def _go_to_original_cwd(self):
        if self._original_cwd:
            os.chdir(self._original_cwd)
        
        self._original_cwd = None

    def close(self):
        self.close_line()
        self._word_size_cache = {}

    def get_html(self, line_css_classes, word_css_classes, word_text) -> str:
        return f"""
        <div id="subtitle-container">
            <div class="{line_css_classes}">
                <span class="{word_css_classes}">{word_text}</span>
            </div>
        </div>
        """
    
    def get_line_css_classes(self, segment_tags: list[Tag], line_tags: list[Tag], line_state: ElementState) -> str:
        css_classes = [self.DEFAULT_CSS_CLASS_FOR_EACH_LINE]
        css_classes.extend([tag.name for tag in segment_tags])
        css_classes.extend([tag.name for tag in line_tags])
        css_classes.append(line_state.value)
        return " ".join(css_classes)
    
    def get_word_css_classes(self, word_tags: list[Tag], index: Optional[int] = None, word_state: Optional[ElementState] = None) -> str:
        css_classes = [self.DEFAULT_CSS_CLASS_FOR_EACH_WORD]
        if index is not None:
            css_classes.append(f"word-{index}-in-line")
        css_classes.extend([tag.name for tag in word_tags])
        if word_state:
            css_classes.append(word_state.value)
        return " ".join(css_classes)
