import os
from .caps_pipeline import CapsPipeline
from pycaps.layout import SubtitleLayoutOptions, LineSplitter, LayoutUpdater, PositionsCalculator
from pycaps.transcriber import AudioTranscriber, BaseSegmentSplitter, WhisperAudioTranscriber, PreviewTranscriber
from typing import Optional
from pycaps.animation import Animation, ElementAnimator
from pycaps.common import ElementType, EventType, VideoQuality, CacheStrategy
from pycaps.tag import TagCondition, SemanticTagger, StructureTagger
from pycaps.effect import TextEffect, ClipEffect, SoundEffect, Effect
from pycaps.logger import logger
from pycaps.renderer import SubtitleRenderer

class CapsPipelineBuilder:

    def __init__(self):
        self._caps_pipeline: CapsPipeline = CapsPipeline()
    
    def with_input_video(self, input_video_path: str) -> "CapsPipelineBuilder":
        if not os.path.exists(input_video_path):
            raise ValueError(f"Input video file not found: {input_video_path}")
        self._caps_pipeline._input_video_path = input_video_path
        return self
    
    def with_output_video(self, output_video_path: str) -> "CapsPipelineBuilder":
        if os.path.exists(output_video_path):
            raise ValueError(f"Output video path already exists: {output_video_path}")
        self._caps_pipeline._output_video_path = output_video_path
        return self

    def with_resources(self, resources_path: str) -> "CapsPipelineBuilder":
        if not os.path.exists(resources_path):
            raise ValueError(f"Resources path does not exist: {resources_path}")
        if not os.path.isdir(resources_path):
            raise ValueError(f"Resources path is not a directory: {resources_path}")
        self._caps_pipeline._resources_dir = resources_path
        return self
    
    def with_video_quality(self, quality: VideoQuality) -> "CapsPipelineBuilder":
        self._caps_pipeline._video_generator.set_video_quality(quality)
        return self
    
    def with_layout_options(self, layout_options: SubtitleLayoutOptions) -> "CapsPipelineBuilder":
        self._caps_pipeline._layout_options = layout_options
        return self
    
    def add_css(self, css_file_path: str) -> "CapsPipelineBuilder":
        if not os.path.exists(css_file_path):
            raise ValueError(f"CSS file not found: {css_file_path}")
        css_content = open(css_file_path, "r", encoding="utf-8").read()
        self._caps_pipeline._renderer.append_css(css_content)
        return self
    
    def add_css_content(self, css_content: str) -> "CapsPipelineBuilder":
        self._caps_pipeline._renderer.append_css(css_content)
        return self

    def with_custom_subtitle_renderer(self, subtitle_renderer: SubtitleRenderer) -> "CapsPipelineBuilder":
        self._caps_pipeline._renderer = subtitle_renderer
        return self
    
    def with_whisper_config(self, language: Optional[str] = None, model_size: str = "base", initial_prompt: Optional[str] = None) -> "CapsPipelineBuilder":
        self._caps_pipeline._transcriber = WhisperAudioTranscriber(model_size=model_size, language=language, initial_prompt=initial_prompt)
        return self
    
    def with_custom_audio_transcriber(self, audio_transcriber: AudioTranscriber) -> "CapsPipelineBuilder":
        self._caps_pipeline._transcriber = audio_transcriber
        return self
    
    def with_cache_strategy(self, cache_strategy: CacheStrategy) -> "CapsPipelineBuilder":
        self._caps_pipeline._cache_strategy = cache_strategy
        return self

    def with_subtitle_data_path(self, subtitle_data_path: str) -> "CapsPipelineBuilder":
        if subtitle_data_path and not os.path.exists(subtitle_data_path):
            raise ValueError(f"Subtitle data file not found: {subtitle_data_path}")
        self._caps_pipeline._subtitle_data_path_for_loading = subtitle_data_path
        return self
    
    def should_save_subtitle_data(self, should_save: bool) -> "CapsPipelineBuilder":
        self._caps_pipeline._should_save_subtitle_data = should_save
        return self
    
    def should_preview_transcription(self, should_preview: bool) -> "CapsPipelineBuilder":
        self._caps_pipeline._should_preview_transcription = should_preview
        return self
    
    def add_segment_splitter(self, segment_splitter: BaseSegmentSplitter) -> "CapsPipelineBuilder":
        self._caps_pipeline._segment_splitters.append(segment_splitter)
        return self
    
    def with_semantic_tagger(self, semantic_tagger: SemanticTagger) -> "CapsPipelineBuilder":
        self._caps_pipeline._semantic_tagger = semantic_tagger
        return self
    
    def with_structure_tagger(self, structure_tagger: StructureTagger) -> "CapsPipelineBuilder":
        self._caps_pipeline._structure_tagger = structure_tagger
        return self  
    
    def add_animation(self, animation: Animation, when: EventType, what: ElementType, tag_condition: Optional[TagCondition] = None) -> "CapsPipelineBuilder":
        self._caps_pipeline._animators.append(ElementAnimator(animation, when, what, tag_condition)) 
        return self
    
    def add_effect(self, effect: Effect) -> "CapsPipelineBuilder":
        if isinstance(effect, TextEffect):
            self._caps_pipeline._text_effects.append(effect)
        elif isinstance(effect, ClipEffect):
            self._caps_pipeline._clip_effects.append(effect)
        elif isinstance(effect, SoundEffect):
            self._caps_pipeline._sound_effects.append(effect)
        return self

    def build(self, preview_time: Optional[tuple[float, float]] = None) -> CapsPipeline:
        if not self._caps_pipeline._input_video_path:
            raise ValueError("Input video path is required")
        if preview_time:
            logger().warning("Generating preview: using dummy text and reducing quality to save time.")
            self.with_video_quality(VideoQuality.LOW)
            self.should_save_subtitle_data(False)
            self.with_custom_audio_transcriber(PreviewTranscriber())
            self._caps_pipeline._preview_time = preview_time
        
        pipeline = self._caps_pipeline
        self._caps_pipeline = CapsPipeline()
        return pipeline