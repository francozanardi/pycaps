import time
import os
from pycaps.transcriber import AudioTranscriber, WhisperAudioTranscriber, BaseSegmentSplitter
from pycaps.renderer import SubtitleRenderer, CssSubtitleRenderer, PictexSubtitleRenderer
from pycaps.video import SubtitleClipsGenerator, VideoGenerator
from pycaps.layout import WordSizeCalculator, PositionsCalculator, LineSplitter, LayoutUpdater
from pycaps.tag import SemanticTagger, StructureTagger
from pycaps.animation import ElementAnimator
from pycaps.layout import SubtitleLayoutOptions
from pycaps.effect import TextEffect, ClipEffect, SoundEffect
from pycaps.common import Document, CacheStrategy
from typing import Optional, List, Tuple
from pathlib import Path
from .subtitle_data_service import SubtitleDataService
from pycaps.transcriber import TranscriptionEditor
from pycaps.logger import logger
from pycaps.utils import time_utils
from pycaps.bootstrap import check_dependencies
import pycaps.api.api_sender as ApiSender

class CapsPipeline:
    def __init__(self):
        # Configuration attributes (set by builder)
        self._transcriber: AudioTranscriber = WhisperAudioTranscriber()
        self._renderer: SubtitleRenderer = CssSubtitleRenderer()
        self._semantic_tagger: SemanticTagger = SemanticTagger()
        self._structure_tagger: StructureTagger = StructureTagger()
        self._segment_splitters: list[BaseSegmentSplitter] = []
        self._animators: List[ElementAnimator] = []
        self._text_effects: List[TextEffect] = []
        self._clip_effects: List[ClipEffect] = []
        self._sound_effects: List[SoundEffect] = []
        self._should_save_subtitle_data: bool = True
        self._subtitle_data_path_for_loading: Optional[str] = None
        self._should_preview_transcription: bool = False
        self._layout_options = SubtitleLayoutOptions()
        self._preview_time: Optional[Tuple[float, float]] = None
        self._input_video_path: Optional[str] = None
        self._output_video_path: Optional[str] = None
        self._resources_dir: Optional[str] = None
        self._cache_strategy: CacheStrategy = CacheStrategy.CSS_CLASSES_AWARE

        # Internal state attributes
        self._video_generator: VideoGenerator = VideoGenerator()
        self._clips_generator: Optional[SubtitleClipsGenerator] = None
        self._word_size_calculator: Optional[WordSizeCalculator] = None
        self._positions_calculator: Optional[PositionsCalculator] = None
        self._line_splitter: Optional[LineSplitter] = None
        self._layout_updater: Optional[LayoutUpdater] = None
        self._video_width: Optional[int] = None
        self._video_height: Optional[int] = None
        self._is_prepared: bool = False

        check_dependencies()

    def prepare(self) -> None:
        """
        Initializes the pipeline environment. This method must be called first.
        It sets up video and audio processing, calculates video dimensions,
        and prepares the renderer.
        """
        if self._is_prepared:
            logger().warning("Pipeline is already prepared. Skipping.")
            return

        logger().info(f"Preparing pipeline for: {self._input_video_path}")
        self._output_video_path = self._ensure_mp4_output_path(self._output_video_path)

        if self._preview_time:
            self._video_generator.set_fragment_time(self._preview_time)
        
        self._video_generator.start(self._input_video_path, self._output_video_path)
        self._preview_time = self._video_generator.get_sanitized_fragment_time()
        self._video_width, self._video_height = self._video_generator.get_video_size()

        resources_dir = Path(self._resources_dir) if self._resources_dir else None
        self._renderer.open(self._video_width, self._video_height, resources_dir, self._cache_strategy)

        ApiSender.start()
        
        # Initialize components that depend on the renderer and layout options
        self._clips_generator = SubtitleClipsGenerator(self._renderer)
        self._word_size_calculator = WordSizeCalculator(self._renderer)
        self._positions_calculator = PositionsCalculator(self._layout_options)
        self._line_splitter = LineSplitter(self._layout_options)
        self._layout_updater = LayoutUpdater(self._layout_options)
        
        self._is_prepared = True
        logger().info("Pipeline prepared successfully.")

    def transcribe(self) -> Document:
        """
        Transcribes the video's audio track.
        
        This method should be called after `prepare()`. It runs the configured
        audio transcriber and returns the initial Document object containing
        word-level timestamps.

        Returns:
            Document: The transcribed document object.
        """
        if not self._is_prepared:
            raise RuntimeError("Pipeline not prepared. Call prepare() before transcribe().")

        logger().info("Transcribing audio...")
        document = self._transcriber.transcribe(self._video_generator.get_audio_path())
        valid_segments = []
        for segment in document.segments:
            if len(segment.get_words()) == 0:
                continue
            valid_segments.append(segment)

            valid_lines = []
            for line in segment.lines:
                if len(line.words) == 0:
                    continue
                valid_lines.append(line)
            segment.lines.set_all(valid_lines)
        
        document.segments.set_all(valid_segments)
        if not document.segments:
            raise RuntimeError("Transcription returned no segments.")
        
        return document

    def process_document(self, document: Document) -> Document:
        """
        Applies all processing steps to a transcribed document.

        This includes splitting segments, calculating layout, applying tags,
        and running text effects. This is the stage where the subtitle
        structure and content are finalized before rendering.

        Args:
            document (Document): The document object to process, typically from `transcribe()`.

        Returns:
            Document: The fully processed document, ready for rendering.
        """
        if not self._is_prepared:
            raise RuntimeError("Pipeline not prepared. Call prepare() before process_document().")

        logger().info("Processing document...")

        # TODO: we should create a document copy to avoid modify received document
        self._cut_document_for_preview_time(document)
        
        logger().debug("Running segment splitters...")
        for splitter in self._segment_splitters:
            splitter.split(document)

        logger().debug("Calculating initial word widths for layout...")
        self._word_size_calculator.calculate(document)

        logger().debug("Splitting segments into lines...")
        self._line_splitter.split_into_lines(document, self._video_width)

        logger().debug("Applying structure and semantic tags...")
        self._structure_tagger.tag(document)
        self._semantic_tagger.tag(document)

        logger().debug("Applying text effects...")
        for effect in self._text_effects:
            effect.run(document)

        if self._should_preview_transcription:
            logger().info("Launching transcription editor...")
            document = TranscriptionEditor().run(document)
            # After editing, structural tags need to be reapplied
            self._structure_tagger.clear(document)
            self._structure_tagger.tag(document)

        if self._should_save_subtitle_data:
            subtitle_data_path = self._output_video_path.replace(".mp4", ".json")
            logger().debug(f"Saving subtitle data to {subtitle_data_path}")
            SubtitleDataService(subtitle_data_path).save(document)

        return document

    def render(self, document: Document) -> None:
        """
        Renders the final video using a fully processed document.

        This method generates the visual clips for subtitles, applies animations
        and effects, and composites everything into the final video file.

        Args:
            document (Document): The processed document from `process_document()`.
        """
        if not self._is_prepared:
            raise RuntimeError("Pipeline not prepared. Call prepare() before render().")

        logger().info("Starting final video render...")
        
        try:
            # TODO: we should create a document copy to avoid modify received document
            self._cut_document_for_preview_time(document)

            logger().info("Generating subtitle clips...")
            self._clips_generator.generate(document)

            logger().debug("Updating layout sizes and positions...")
            self._layout_updater.update_max_sizes(document)
            self._positions_calculator.calculate(document, self._video_width, self._video_height)
            self._layout_updater.update_max_positions(document)

            logger().info("Applying clip and sound effects...")
            for effect in self._clip_effects:
                effect.set_renderer(self._renderer)
                effect.run(document)
            for effect in self._sound_effects:
                effect.run(document)

            logger().info("Applying animations...")
            for animator in self._animators:
                animator.run(document)

            logger().info("Generating final video file...")
            self._video_generator.generate(document)

            logger().info(f"Video rendered successfully to {self._output_video_path}!")

        except Exception as e:
            logger().error(f"An error occurred during rendering: {e}")
            raise e
        finally:
            self.close()
            logger().debug(f"Render and cleanup finished.")

    def close(self) -> None:
        """
        Cleans up all resources used by the pipeline, such as temporary files
        and renderer instances. Should be called after processing is complete.
        """
        logger().debug("Cleaning up pipeline resources...")
        self._video_generator.close()
        self._renderer.close()
        ApiSender.close()
        self._is_prepared = False

    def run(self) -> None:
        """
        Runs the entire pipeline from start to finish.
        
        This is a convenience method that calls `prepare`, `transcribe`,
        `process_document`, and `render` in sequence.
        """
        start_time = time.time()
        try:
            self.prepare()
            
            # If a subtitle data file is provided, load it and skip transcription/processing.
            if self._subtitle_data_path_for_loading:
                logger().info(f"Loading subtitle data from: {self._subtitle_data_path_for_loading}")
                document = SubtitleDataService(self._subtitle_data_path_for_loading).load()
                self._cut_document_for_preview_time(document)
            else:
                initial_document = self.transcribe()
                document = self.process_document(initial_document)
            
            self.render(document)
        
        finally:
            logger().info(f"Total pipeline execution time: {time.time() - start_time:.2f} seconds")

    def _cut_document_for_preview_time(self, document: Document):
        if not self._preview_time:
            return
        is_in_preview_time = lambda e: time_utils.times_intersect(self._preview_time[0], self._preview_time[1], e.time.start, e.time.end)
        for segment in document.segments[:]:
            if not is_in_preview_time(segment):
                document.segments.remove(segment)
                continue
            for line in segment.lines[:]:
                if not is_in_preview_time(line):
                    segment.lines.remove(line)
                    continue
                for word in line.words[:]:
                    if not is_in_preview_time(word):
                        line.words.remove(word)

    def _ensure_mp4_output_path(self, output_path: Optional[str]) -> str:
        if output_path is None:
            return f"output_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
        base, _ = os.path.splitext(output_path)
        return base + ".mp4"
