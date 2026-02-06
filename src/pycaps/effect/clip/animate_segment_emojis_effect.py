from .clip_effect import ClipEffect
from pycaps.common import Document, WordClip
from pycaps.tag import TagConditionFactory, BuiltinTag
from pycaps.logger import logger
import os
import requests
import zipfile
import io
from pathlib import Path
from tqdm import tqdm
from platformdirs import user_cache_dir

class AnimateSegmentEmojisEffect(ClipEffect):

    CURRENT_ASSETS_VERSION = "2.0.0"

    ASSETS_ZIP_URL = "https://github.com/francozanardi/pycaps/releases/download/emoji-assets-v2/animated_emojis.zip"
    ASSETS_VERSION_URL = "https://github.com/francozanardi/pycaps/releases/download/emoji-assets-v2/version.txt"

    CACHE_DIR = Path(user_cache_dir("pycaps")) / "assets" / "emojis"
    VERSION_FILE = CACHE_DIR / "version.txt"
    
    def run(self, document: Document) -> None:
        self._ensure_assets_are_downloaded()

        tag_condition = TagConditionFactory.HAS(BuiltinTag.EMOJI_FOR_SEGMENT)
        for word in document.get_words():
            if not tag_condition.evaluate(list(word.semantic_tags)):
                continue
            for clip in word.clips:
                self.__animate_emoji_if_possible(clip)

    def _ensure_assets_are_downloaded(self):
        local_version = self._get_local_version()

        if local_version == self.CURRENT_ASSETS_VERSION:
            return
        
        logger().info(f"Downloading animated emoji pack v{self.CURRENT_ASSETS_VERSION}...")
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

        if self.CACHE_DIR.exists():
            import shutil
            shutil.rmtree(self.CACHE_DIR)
        
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

        try:
            response = requests.get(self.ASSETS_ZIP_URL, stream=True)
            response.raise_for_status()

            total_size_in_bytes = int(response.headers.get('content-length', 0))
            block_size = 1024
            progress_bar = tqdm(
                total=total_size_in_bytes, 
                unit='iB', 
                unit_scale=True,
                desc="Emojis"
            )
            file_buffer = io.BytesIO()
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file_buffer.write(data)

            progress_bar.close()

            logger().info("Unzipping assets...")

            file_buffer.seek(0)
            with zipfile.ZipFile(file_buffer) as z:
                z.extractall(self.CACHE_DIR)

            self.VERSION_FILE.write_text(self.CURRENT_ASSETS_VERSION)
            logger().info("Emoji pack downloaded successfully.")

        except Exception as e:
            if 'progress_bar' in locals() and not progress_bar.disable:
                progress_bar.close()

            logger().error(f"Failed to download emoji pack. Animated emojis will be disabled. Error: {e}")
            if self.CACHE_DIR.exists():
                import shutil
                shutil.rmtree(self.CACHE_DIR)

    def _get_local_version(self) -> str:
        if not self.VERSION_FILE.exists():
            return "0.0.0"
        return self.VERSION_FILE.read_text().strip()

    def __animate_emoji_if_possible(self, clip: WordClip) -> None:
        from movielite import AlphaVideoClip

        emoji = clip.get_word().text
        filename = self._emoji_to_unicode_hex(emoji) + ".gif"
        animated_emoji_gif = self.CACHE_DIR / filename
        if not os.path.isfile(animated_emoji_gif):
            return
    
        clip.media_clip = AlphaVideoClip(str(animated_emoji_gif), clip.media_clip.start, clip.media_clip.duration)
        clip.media_clip.set_position((clip.layout.position.x, clip.layout.position.y))
        clip.media_clip.set_size(height=clip.layout.size.height)

    def _emoji_to_unicode_hex(self, emoji: str) -> str:
        codepoints = [f"{ord(char):x}" for char in emoji]
        return "_".join(codepoints)
