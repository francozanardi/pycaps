from pathlib import Path
import tempfile
from typing import Optional, TYPE_CHECKING, Tuple, Dict
from pycaps.common import Word, ElementState, Line, Size, CacheStrategy
import shutil
from .rendered_image_cache import RenderedImageCache
from .playwright_screenshot_capturer import PlaywrightScreenshotCapturer
from .renderer_page import RendererPage
from .letter_size_cache import LetterSizeCache
from .subtitle_renderer import SubtitleRenderer

if TYPE_CHECKING:
    from playwright.sync_api import Page, Browser, Playwright
    from PIL.Image import Image

class CssSubtitleRenderer(SubtitleRenderer):

    BASE_DEVICE_SCALE_FACTOR: float = 2.0
    REFERENCE_VIDEO_HEIGHT: int = 1280
    MIN_SCALE_MODIFIER: float = 0.25
    MAX_SCALE_MODIFIER: float = 5.0
    DEFAULT_VIEWPORT_HEIGHT_RATIO: float = 0.25
    DEFAULT_MIN_VIEWPORT_HEIGHT: int = 150

    def __init__(self, browser: Optional['Browser'] = None):
        """
        Renders subtitles using HTML and CSS via Playwright.

        Args:
            browser: (Optional) A pre-launched Playwright browser instance.
        """

        self._playwright_context: Optional[Playwright] = None
        self._browser: Optional['Browser'] = browser
        self._page: Optional[Page] = None
        self._tempdir: Optional[tempfile.TemporaryDirectory] = None
        self._custom_css: str = ""
        self._cache_strategy = CacheStrategy.CSS_CLASSES_AWARE
        self._image_cache: RenderedImageCache = None
        self._letter_size_cache: LetterSizeCache = None
        self._current_line: Optional[Line] = None
        self._current_line_state: Optional[ElementState] = None
        self._renderer_page: RendererPage = RendererPage()
        self._device_scale_factor: float = self.BASE_DEVICE_SCALE_FACTOR

    def _calculate_scale_modifier(self, video_height: int) -> float:
        """Calculates a scale modifier based on video height relative to reference."""
        modifier = video_height / self.REFERENCE_VIDEO_HEIGHT
        return max(self.MIN_SCALE_MODIFIER, min(self.MAX_SCALE_MODIFIER, modifier))

    def append_css(self, css: str):
        self._custom_css += css

    def open(self, video_width: int, video_height: int, resources_dir: Optional[Path] = None, cache_strategy: CacheStrategy = CacheStrategy.CSS_CLASSES_AWARE):
        """Initializes Playwright and loads the base HTML page."""
        from playwright.sync_api import sync_playwright

        if self._page:
            raise RuntimeError("Renderer is already open. Call close() first.")

        scale_modifier = self._calculate_scale_modifier(video_height)
        self._device_scale_factor = self.BASE_DEVICE_SCALE_FACTOR * scale_modifier
        calculated_vp_height = max(self.DEFAULT_MIN_VIEWPORT_HEIGHT, int(video_height * self.DEFAULT_VIEWPORT_HEIGHT_RATIO))

        self._cache_strategy = cache_strategy
        self._image_cache = RenderedImageCache(self._custom_css, self._cache_strategy)
        self._letter_size_cache = LetterSizeCache(self._custom_css)
        self._tempdir = tempfile.TemporaryDirectory()
        if not self._browser:
            self._playwright_context = sync_playwright().start()
            try:
                self._browser = self._playwright_context.chromium.launch()
            except Exception as e:
                raise RuntimeError(
                    "Playwright Chromium browser is not installed or failed to launch.\n"
                    "You can install it by running:\n\n"
                    "    playwright install chromium\n\n"
                    f"Full error:\n{str(e)}"
                ) from e
        context = self._browser.new_context(device_scale_factor=self._device_scale_factor, viewport={"width": video_width, "height": calculated_vp_height})
        self._page = context.new_page()
        self._copy_resources_to_tempdir(resources_dir)
        path = self._create_html_page()
        self._page.goto(path.as_uri())
        self._page.wait_for_load_state('networkidle')

    def _create_html_page(self) -> Path:
        if not self._tempdir:
            raise RuntimeError("self.tempdir is not defined. Do you call open() first?")
        
        html_template = self._renderer_page.get_html(custom_css=self._custom_css)
        html_path = Path(self._tempdir.name) / "renderer_base.html"
        html_path.write_text(html_template, encoding="utf-8")
        return html_path

    def _copy_resources_to_tempdir(self, resources_dir: Optional[Path] = None) -> None:
        if not self._tempdir:
            raise RuntimeError("Temp directory must be initialized before copying resources.")
        if not resources_dir:
            return
        if not resources_dir.exists():
            raise RuntimeError(f"Resources directory does not exist: {resources_dir}")
        if not resources_dir.is_dir():
            raise RuntimeError(f"Resources path is not a directory: {resources_dir}")

        destination = Path(self._tempdir.name)
        shutil.copytree(resources_dir, destination, dirs_exist_ok=True)

    def open_line(self, line: Line, line_state: ElementState):
        if not self._page:
            raise RuntimeError("Renderer is not open. Call open() first.")
        if self._current_line:
            raise RuntimeError("A line is already open. Call close_line() first.")
        
        self._current_line = line
        self._current_line_state = line_state

        script = f"""
        ([text, cssClassesForLine, cssClassesForWords]) => {{
            const line = document.querySelector('.{RendererPage.DEFAULT_CSS_CLASS_FOR_EACH_LINE}');
            line.innerHTML = '';
            line.className = cssClassesForLine;
            const words = text.split(' ');
            words.forEach((word, index) => {{
                const wordElement = document.createElement('span');
                const cssClassesForWord = cssClassesForWords[index];
                wordElement.textContent = word;
                wordElement.className = cssClassesForWord;
                line.appendChild(wordElement);
            }});
        }}
        """
        line_css_classes = self._renderer_page.get_line_css_classes(line.get_segment().get_tags(), line.get_tags(), line_state)
        words_css_classes = [self._renderer_page.get_word_css_classes(word.get_tags(), index) for index, word in enumerate(line.words)]
        self._page.evaluate(script, [line.get_text(), line_css_classes, words_css_classes])
   
    def render_word(self, index: int, word: Word, state: ElementState, first_n_letters: Optional[int] = None) -> Optional['Image']:
        if not self._page:
            raise RuntimeError("Renderer is not open. Call open() first.")
        if not self._current_line:
            raise RuntimeError("No line is open. Call open_line() first.")
        
        line_css_classes = self._renderer_page.get_line_css_classes(self._current_line.get_segment().get_tags(), self._current_line.get_tags(), self._current_line_state)
        word_css_classes = self._renderer_page.get_word_css_classes(word.get_tags(), index, state)
        all_css_classes = line_css_classes + " " + word_css_classes
        if self._image_cache.has(index, word.text, all_css_classes, first_n_letters):
            return self._image_cache.get(index, word.text, all_css_classes, first_n_letters)

        # Why are we doing this?
        # When the typewriting effect is applied, we need to render the word partially (first n letters).
        # However, if we have some line background that depends on the size (like a gradient),
        # since the word was cropped, the background will be incorrect.
        # It can be specially noticeable in the last word of the line.
        # The same would happen if we use border-radius, since we crop the word,
        # it will show the rounded corners in each word fragment of the last word
        # To fix this, we create a new span with the remaining part of the word and make it invisible.
        # This way, the line is rendered with the final width it will have, and the background will be correct.

        script = f"""
        ([index, state, wordText, first_n_letters]) => {{
            const word = document.querySelector(`.word-${{index}}-in-line`);
            const wordCodePoints = Array.from(wordText); // to avoid issues with multibyte characters
            word.textContent = wordCodePoints.slice(0, first_n_letters).join('');
            word.classList.add(state);

            // the rest remains there but invisible
            if (first_n_letters < wordCodePoints.length) {{
                remaining_word = word.dataset.isNextNodeRemaining ? word.nextSibling : document.createElement('span');
                remaining_word.textContent = wordCodePoints.slice(first_n_letters).join('');
                remaining_word.className = word.className;
                remaining_word.style.visibility = 'hidden';
                if (!word.dataset.isNextNodeRemaining) {{
                    word.parentNode.insertBefore(remaining_word, word.nextSibling);
                    word.dataset.isNextNodeRemaining = true;
                }}
            }} else if (word.dataset.isNextNodeRemaining) {{
                word.parentNode.removeChild(word.nextSibling);
                delete word.dataset.isNextNodeRemaining;
            }}

            return word.getBoundingClientRect();
        }}
        """
        word_bounding_box = self._page.evaluate(script, [index, state.value, word.text, first_n_letters if first_n_letters else len(word.text)])
        try:
            if word_bounding_box["width"] <= 0 or word_bounding_box["height"] <= 0:
                # HTML element is not visible (probably hidden by CSS).
                self._image_cache.set(index, word.text, all_css_classes, first_n_letters, None)
                return None

            image = PlaywrightScreenshotCapturer.capture(self._page, word_bounding_box)
            self._image_cache.set(index, word.text, all_css_classes, first_n_letters, image)
            return image
        except Exception as e:
            raise RuntimeError(f"Error rendering word '{word.text}': {e}")
        finally:
            self._page.evaluate(f"""
            ([index, state]) => {{
                const word = document.querySelector(`.word-${{index}}-in-line`);
                word.classList.remove(state);
            }}
            """, [index, state.value])
    
    def close_line(self):
        if not self._page:
            raise RuntimeError("Renderer is not open. Call open() first.")
        if not self._current_line:
            raise RuntimeError("No line is open. Call open_line() first.")
        
        self._current_line = None
        self._current_line_state = None
        
    def get_word_size(self, word: Word, line_state: ElementState, word_state: ElementState) -> Tuple[int, int]:
        if not self._page:
            raise RuntimeError("Renderer is not open. Call open() first.")
        if self._current_line:
            raise RuntimeError("A line process is in progress. Call close_line() first.")
        
        line_css_classes = self._renderer_page.get_line_css_classes(word.get_segment().get_tags(), word.get_line().get_tags(), line_state)
        word_css_classes = self._renderer_page.get_word_css_classes(word.get_tags(), word_state=word_state)
        all_css_classes = line_css_classes + " " + word_css_classes

        cached_letters_size = {}
        not_cached_letters_size = []
        # All letters are measured without padding/borders/etc, the "NON_CONTENT_WIDTH" is used to measure the paddings/borders/etc
        # So, each word must have the "NON_CONTENT_WIDTH" to include its padding/border/etc 
        letters = list(word.text) + ["NON_CONTENT_WIDTH"]
        for letter in letters:
            if self._letter_size_cache.has(letter, all_css_classes):
                cached_letters_size[letter] = self._letter_size_cache.get(letter, all_css_classes)
            else:
                not_cached_letters_size.append(letter)

        cached_width = sum(s.width for s in cached_letters_size.values())
        cached_height = max(s.height for s in cached_letters_size.values()) if cached_letters_size else 0
        if len(not_cached_letters_size) == 0:
            return int(cached_width * self._device_scale_factor), int(cached_height * self._device_scale_factor)

        script = f"""
        ([letters, lineCssClasses, wordCssClasses]) => {{
            const line = document.querySelector('.{RendererPage.DEFAULT_CSS_CLASS_FOR_EACH_LINE}');
            line.innerHTML = '';
            line.className = lineCssClasses;
            const wordElement = document.createElement('span');
            wordElement.textContent = '';
            wordElement.className = wordCssClasses;
            line.appendChild(wordElement);
            const emptyWidth = wordElement.getBoundingClientRect().width;
            letters_size = {{}}
            for (const letter of letters) {{
                wordElement.textContent = letter === "NON_CONTENT_WIDTH" ? "" : letter;
                const box = wordElement.getBoundingClientRect();
                // we exclude the extra width (paddings, borders, etc) for each letter
                // it is only taken into account when we want to measure the "NON_CONTENT_WIDTH"
                const width = letter === "NON_CONTENT_WIDTH" ? box.width : box.width - emptyWidth
                letters_size[letter] = {{width: width, height: box.height}};
            }}
            return letters_size;
        }}
        """
        new_letters_size: Dict = self._page.evaluate(script, [not_cached_letters_size, line_css_classes, word_css_classes])
        for letter, size in new_letters_size.items():
            new_letters_size[letter] = Size(size['width'], size['height'])

        self._letter_size_cache.set_all(new_letters_size, all_css_classes)
        width = cached_width + sum(s.width for s in new_letters_size.values())
        height = max(cached_height, max(s.height for s in new_letters_size.values())) 

        # This is not precise, but it is enough to create the basic structure
        return int(width * self._device_scale_factor), int(height * self._device_scale_factor)

    def close(self):
        """Closes Playwright and cleans up resources."""
        if self._playwright_context:
            if self._browser:
                self._browser.close()
                self._browser = None
            self._playwright_context.stop()
            self._playwright_context = None
        if self._tempdir:
            self._tempdir.cleanup()
            self._tempdir = None
        self._page = None

    def __enter__(self):
        # Video dimensions are expected to be provided via an explicit call to open().
        # Using this class as a context manager ensures close() is called,
        # but open() must still be managed by the user if specific dimensions are needed upfront.
        # Typical usage:
        # with HTMLCSSRenderer(...) as renderer:
        #    renderer.open(video_w, video_h) # Call open with dimensions
        #    ...
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 
