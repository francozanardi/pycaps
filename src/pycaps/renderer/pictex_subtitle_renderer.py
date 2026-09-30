from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple, Any, Dict, Union, Set
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

    def __init__(
        self,
        custom_css: Optional[Union[str, Dict[str, Any]]] = None,
        styles: Optional[Union[str, Dict[str, Any]]] = None,
        template: Optional[Any] = None,
        resources_dir: Optional[Union[Path, str]] = None,
        video_width: Optional[int] = None,
        video_height: Optional[int] = None,
        scale_factor: Optional[float] = None,
    ):
        super().__init__()
        self._custom_css: str = ""
        self._current_line: Optional[Line] = None
        self._current_line_state: Optional[ElementState] = None
        self._resources_dir: Optional[Path] = Path(resources_dir) if resources_dir else None
        self._original_cwd: Optional[Path] = None
        self._cache_strategy: CacheStrategy = CacheStrategy.CSS_CLASSES_AWARE
        self._image_cache: Optional[RenderedImageCache] = None
        self._video_width: Optional[int] = video_width
        self._video_height: Optional[int] = video_height
        self._scale_factor: float = scale_factor if scale_factor is not None else self.BASE_SCALE_FACTOR
        self._custom_scale_factor_set: bool = scale_factor is not None

        if video_height is not None and scale_factor is None:
            self._scale_factor = self.BASE_SCALE_FACTOR * self._calculate_scale_modifier(video_height)

        if template is not None:
            self.apply_template(template)
        if custom_css is not None:
            self.append_css(custom_css)
        if styles is not None:
            self.append_css(styles)

    @classmethod
    def from_template(cls, template: Any) -> "PictexSubtitleRenderer":
        """Creates a PictexSubtitleRenderer initialized with styles and resources from a Template or TemplateLoader."""
        renderer = cls()
        renderer.apply_template(template)
        return renderer

    def apply_template(self, template: Any) -> "PictexSubtitleRenderer":
        """Captures and applies styles and resources from a template or template loader."""
        from pycaps.template import TemplateLoader
        if isinstance(template, TemplateLoader):
            loader = template
        else:
            loader = TemplateLoader(template)
        css = loader.get_css()
        if css:
            self.append_css(css)
        resources_path = loader.get_resources_path()
        if resources_path and not self._resources_dir:
            self.resources_dir = Path(resources_path)
        return self

    @staticmethod
    def _styles_to_css(styles: Union[str, Dict[str, Any]]) -> str:
        """Converts a style dictionary or string into valid CSS block(s)."""
        if isinstance(styles, str):
            return styles
        if not isinstance(styles, dict):
            raise TypeError(f"Expected str or dict for styles, got {type(styles)}")

        css_blocks = []
        flat_props = {}
        for key, val in styles.items():
            if isinstance(val, dict):
                selector = key.strip()
                if not (selector.startswith((".", "#", "@", ":")) or " " in selector or ">" in selector):
                    selector = f".{selector}"
                rules = "; ".join(f"{prop.strip()}: {str(v).strip()}" for prop, v in val.items())
                css_blocks.append(f"{selector} {{ {rules}; }}")
            else:
                flat_props[key] = val
        if flat_props:
            rules = "; ".join(f"{prop.strip()}: {str(v).strip()}" for prop, v in flat_props.items())
            css_blocks.append(f".{PictexSubtitleRenderer.DEFAULT_CSS_CLASS_FOR_EACH_WORD} {{ {rules}; }}")
        return "\n".join(css_blocks) + "\n"

    @property
    def custom_css(self) -> str:
        return self._custom_css

    @custom_css.setter
    def custom_css(self, value: Union[str, Dict[str, Any]]):
        self._custom_css = ""
        self.append_css(value)

    @property
    def resources_dir(self) -> Optional[Path]:
        return self._resources_dir

    @resources_dir.setter
    def resources_dir(self, value: Optional[Union[Path, str]]):
        self._resources_dir = Path(value) if value else None

    @property
    def scale_factor(self) -> float:
        return self._scale_factor

    @scale_factor.setter
    def scale_factor(self, value: float):
        self._scale_factor = value
        self._custom_scale_factor_set = True

    @property
    def video_width(self) -> Optional[int]:
        return self._video_width

    @property
    def video_height(self) -> Optional[int]:
        return self._video_height

    @property
    def video_dimensions(self) -> Tuple[Optional[int], Optional[int]]:
        return (self._video_width, self._video_height)

    def set_styles(self, styles: Union[str, Dict[str, Any]]) -> "PictexSubtitleRenderer":
        self._custom_css = ""
        self.append_css(styles)
        return self

    def add_styles(self, styles: Union[str, Dict[str, Any]]) -> "PictexSubtitleRenderer":
        self.append_css(styles)
        return self

    def _calculate_scale_modifier(self, video_height: int) -> float:
        """Calculates a scale modifier based on video height relative to reference."""
        modifier = video_height / self.REFERENCE_VIDEO_HEIGHT
        return max(self.MIN_SCALE_MODIFIER, min(self.MAX_SCALE_MODIFIER, modifier))

    def append_css(self, css: Union[str, Dict[str, Any]]):
        css_str = self._styles_to_css(css) if isinstance(css, dict) else css
        self._custom_css += css_str
        if self._image_cache is not None:
            self._image_cache = RenderedImageCache(self._custom_css, self._cache_strategy)

    def _ensure_image_cache(self):
        if self._image_cache is None:
            self._image_cache = RenderedImageCache(self._custom_css, self._cache_strategy)

    def open(self, video_width: int, video_height: int, resources_dir: Optional[Path] = None, cache_strategy: CacheStrategy = CacheStrategy.CSS_CLASSES_AWARE):
        self._video_width = video_width
        self._video_height = video_height
        if not self._custom_scale_factor_set:
            scale_modifier = self._calculate_scale_modifier(video_height)
            self._scale_factor = self.BASE_SCALE_FACTOR * scale_modifier
        if resources_dir is not None:
            self._resources_dir = Path(resources_dir) if isinstance(resources_dir, str) else resources_dir
        self._cache_strategy = cache_strategy
        self._image_cache = RenderedImageCache(self._custom_css, self._cache_strategy)

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
        
        self._ensure_image_cache()

        segment_tags = self._current_line.get_segment().get_tags() if self._current_line.get_segment() else set()
        line_tags = self._current_line.get_tags() if self._current_line else set()
        line_css_classes = self.get_line_css_classes(segment_tags, line_tags, self._current_line_state)
        word_css_classes = self.get_word_css_classes(word.get_tags(), index, state)
        all_css_classes = line_css_classes + " " + word_css_classes
        if self._image_cache.has(index, word.text, all_css_classes, first_n_letters):
            return self._image_cache.get(index, word.text, all_css_classes, first_n_letters)

        self._use_resources_dir_as_cwd()
        try:
            text = word.text[:first_n_letters] if first_n_letters else word.text
            renderer = Html2Pic(self.get_html(line_css_classes, word_css_classes, text), self._custom_css)
            canvas, root_element = renderer._translator.translate(renderer.styled_tree, renderer.font_registry)
            if root_element is None:
                self._image_cache.set(index, word.text, all_css_classes, first_n_letters, None)
                return None
            try:
                image = canvas.render(root_element, crop_mode=CropMode.CONTENT_BOX, scale_factor=self._scale_factor)
                pillow_image = image.to_pillow()
                self._image_cache.set(index, word.text, all_css_classes, first_n_letters, pillow_image)
                return pillow_image
            except Exception:
                self._image_cache.set(index, word.text, all_css_classes, first_n_letters, None)
                return None
        except Exception:
            self._image_cache.set(index, word.text, all_css_classes, first_n_letters, None)
            return None
        finally:
            self._go_to_original_cwd()

    def close_line(self):
        self._current_line = None
        self._current_line_state = None
 
    def get_word_size(self, word: Word, line_state: ElementState, word_state: ElementState) -> Tuple[int, int]:
        from pictex import CropMode
        from html2pic import Html2Pic
        
        if self._current_line:
            raise RuntimeError("A line process is in progress. Call close_line() first.")

        self._ensure_image_cache()

        segment_tags = word.get_segment().get_tags() if (word.get_line() and word.get_segment()) else set()
        line_tags = word.get_line().get_tags() if word.get_line() else set()
        line_css_classes = self.get_line_css_classes(segment_tags, line_tags, line_state)
        word_css_classes = self.get_word_css_classes(word.get_tags(), word_state=word_state)
        all_css_classes = line_css_classes + " " + word_css_classes
        if self._image_cache.has(-1, word.text, all_css_classes, None):
            image = self._image_cache.get(-1, word.text, all_css_classes, None)
            if image is None:
                return (0, 0)
            return (image.width, image.height)

        self._use_resources_dir_as_cwd()
        try:
            renderer = Html2Pic(self.get_html(line_css_classes, word_css_classes, word.text), self._custom_css)
            canvas, root_element = renderer._translator.translate(renderer.styled_tree, renderer.font_registry)
            if root_element is None:
                self._image_cache.set(-1, word.text, all_css_classes, None, None)
                return (0, 0)
            try:
                image = canvas.render(root_element, crop_mode=CropMode.CONTENT_BOX, scale_factor=self._scale_factor)
                pillow_image = image.to_pillow()
                self._image_cache.set(-1, word.text, all_css_classes, None, pillow_image)
                return (image.width, image.height)
            except Exception:
                self._image_cache.set(-1, word.text, all_css_classes, None, None)
                return (0, 0)
        except Exception:
            self._image_cache.set(-1, word.text, all_css_classes, None, None)
            return (0, 0)
        finally:
            self._go_to_original_cwd()
    
    def _use_resources_dir_as_cwd(self):
        if self._resources_dir and os.path.exists(self._resources_dir):
            self._original_cwd = os.getcwd()
            os.chdir(self._resources_dir)

    def _go_to_original_cwd(self):
        if self._original_cwd:
            try:
                os.chdir(self._original_cwd)
            except Exception:
                pass
        self._original_cwd = None

    def close(self):
        self.close_line()

    def get_html(self, line_css_classes, word_css_classes, word_text) -> str:
        return f"""
        <div id="subtitle-container">
            <div class="{line_css_classes}">
                <span class="{word_css_classes}">{word_text}</span>
            </div>
        </div>
        """
    
    def get_line_css_classes(self, segment_tags: Union[list[Tag], Set[Tag]], line_tags: Union[list[Tag], Set[Tag]], line_state: ElementState) -> str:
        css_classes = [self.DEFAULT_CSS_CLASS_FOR_EACH_LINE]
        css_classes.extend([tag.name for tag in segment_tags])
        css_classes.extend([tag.name for tag in line_tags])
        css_classes.append(line_state.value)
        return " ".join(css_classes)
    
    def get_word_css_classes(self, word_tags: Union[list[Tag], Set[Tag]], index: Optional[int] = None, word_state: Optional[ElementState] = None) -> str:
        css_classes = [self.DEFAULT_CSS_CLASS_FOR_EACH_WORD]
        if index is not None:
            css_classes.append(f"word-{index}-in-line")
        css_classes.extend([tag.name for tag in word_tags])
        if word_state:
            css_classes.append(word_state.value)
        return " ".join(css_classes)
