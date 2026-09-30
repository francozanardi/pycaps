import json
from .caps_pipeline_builder import CapsPipelineBuilder
from .caps_pipeline import CapsPipeline
from pycaps.transcriber import LimitByWordsSplitter, LimitByCharsSplitter, SplitIntoSentencesSplitter
from pycaps.tag import TagConditionFactory, TagCondition
from pycaps.effect import *
from pycaps.animation import *
from .json_schema import JsonSchema, AnimationConfig
from pydantic import ValidationError
from pycaps.tag import SemanticTagger
from pycaps.common import Tag
from typing import overload, Literal
import os

class JsonConfigLoader:
    def __init__(self, json_path: str) -> None:
        with open(json_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        self._json_path = json_path
        self._base_path = os.path.dirname(self._json_path)

    @overload
    def load(self, should_build_pipeline: Literal[True] = True) -> CapsPipeline:
        ...
    @overload
    def load(self, should_build_pipeline: Literal[False]) -> CapsPipelineBuilder:
        ...
    def load(self, should_build_pipeline: bool = True) -> CapsPipeline | CapsPipelineBuilder:
        try:
            self._config = JsonSchema(**self._data)
            self._builder = CapsPipelineBuilder()
            if self._config.css:
                self._builder.add_css(os.path.join(self._base_path, self._config.css))
            if self._config.input:
                self._builder.with_input_video(os.path.join(self._base_path, self._config.input))
            if self._config.output:
                self._builder.with_output_video(self._config.output)
            if self._config.resources:
                self._builder.with_resources(os.path.join(self._base_path, self._config.resources))
            if self._config.cache_strategy:
                self._builder.with_cache_strategy(self._config.cache_strategy)

            self._load_video_config()
            self._load_whisper_config()
            self._load_layout_options()
            self._load_segment_splitters()
            self._load_effects()
            self._load_sound_effects()
            self._load_animations()
            self._load_semantic_tagger()
            if should_build_pipeline:
                return self._builder.build()
            else:
                return self._builder
        except ValidationError as e:
            raise ValueError(f"Invalid config: {e}")

    def _load_video_config(self) -> None:
        if self._config.video is None:
            return
        video_data = self._config.video
        if video_data.quality is not None:
            self._builder.with_video_quality(video_data.quality)

    def _load_whisper_config(self) -> None:
        if self._config.whisper is None:
            return
        whisper_data = self._config.whisper
        self._builder.with_whisper_config(
            language=whisper_data.language,
            model_size=whisper_data.model,
            backend=whisper_data.backend
        )

    def _load_layout_options(self) -> None:
        if self._config.layout is None:
            return
        self._builder.with_layout_options(self._config.layout)

    def _load_segment_splitters(self) -> None:
        for splitter in self._config.splitters:
            match splitter.type:
                case "limit_by_words":
                    self._builder.add_segment_splitter(LimitByWordsSplitter(splitter.limit))
                case "limit_by_chars":
                    self._builder.add_segment_splitter(LimitByCharsSplitter(splitter.max_chars, splitter.min_chars, splitter.avoid_finishing_segment_with_word_shorter_than))
                case "split_into_sentences":
                    self._builder.add_segment_splitter(SplitIntoSentencesSplitter(splitter.sentences_separators))
                case _:
                    raise ValueError(f"Invalid segment splitter type: {splitter.type}")

    def _load_effects(self) -> None:
        for effect in self._config.effects:
            match effect.type:
                case "emoji_in_segment":
                    self._builder.add_effect(EmojiInSegmentEffect(effect.chance_to_apply, effect.align, effect.ignore_segments_with_duration_less_than, effect.max_uses_of_each_emoji, effect.max_consecutive_segments_with_emoji))
                case "emoji_in_word":
                    self._builder.add_effect(EmojiInWordEffect(effect.emojis, self._build_tag_condition(effect.tag_condition), effect.avoid_use_same_emoji_in_a_row))
                case "remove_punctuation_marks":
                    self._builder.add_effect(RemovePunctuationMarksEffect(effect.punctuation_marks, effect.exception_marks))
                case "typewriting":
                    self._builder.add_effect(TypewritingEffect(self._build_tag_condition(effect.tag_condition)))
                case "animate_segment_emojis":
                    self._builder.add_effect(AnimateSegmentEmojisEffect())

    def _load_sound_effects(self) -> None:
        for effect in self._config.sound_effects:
            match effect.type:
                case "preset":
                    sound = BuiltinSound.get_by_name(effect.name)
                    if sound is None:
                        raise ValueError(f"Invalid preset sound: {effect.name}")
                    self._builder.add_effect(
                        SoundEffect(
                            sound,
                            effect.when,
                            effect.what,
                            self._build_tag_condition(effect.tag_condition),
                            effect.offset,
                            effect.volume,
                            effect.interpret_consecutive_words_as_one
                        )
                    )
                case "custom":
                    self._builder.add_effect(
                        SoundEffect(
                            Sound(effect.path, os.path.join(self._base_path, effect.path)),
                            effect.when,
                            effect.what,
                            self._build_tag_condition(effect.tag_condition),
                            effect.offset,
                            effect.volume,
                            effect.interpret_consecutive_words_as_one
                        )
                    )

    def _load_animations(self) -> None:
        for animation_config in self._config.animations:
            tag_condition = self._build_tag_condition(animation_config.tag_condition)
            animation = self._build_animation(animation_config)
            self._builder.add_animation(animation, animation_config.when, animation_config.what, tag_condition)

    def _build_tag_condition(self, tag_condition: str) -> TagCondition:
        if tag_condition:
            return TagConditionFactory.parse(tag_condition)
        return TagConditionFactory.TRUE()
    
    def _build_animation(self, animation: AnimationConfig) -> Animation:
        match animation.type:
            case "fade_in":
                return FadeIn(animation.duration, animation.delay)
            case "fade_out":
                return FadeOut(animation.duration, animation.delay)
            case "zoom_in":
                return ZoomIn(animation.duration, animation.delay)
            case "zoom_out":
                return ZoomOut(animation.duration, animation.delay)
            case "pop_in":
                return PopIn(animation.duration, animation.delay)
            case "pop_out":
                return PopOut(animation.duration, animation.delay)
            case "pop_in_bounce":
                return PopInBounce(animation.duration, animation.delay)
            case "slide_in":
                return SlideIn(animation.direction, animation.duration, animation.delay)
            case "slide_out":
                return SlideOut(animation.direction, animation.duration, animation.delay)
            case "zoom_in_primitive":
                return ZoomInPrimitive(
                    animation.duration,
                    animation.delay,
                    self._build_transformer(animation.transformer),
                    animation.init_scale,
                    animation.overshoot
                )
            case "pop_in_primitive":
                return PopInPrimitive(
                    animation.duration,
                    animation.delay,
                    self._build_transformer(animation.transformer),
                    animation.init_scale,
                    animation.min_scale,
                    animation.min_scale_at,
                    animation.overshoot
                )
            case "slide_in_primitive":
                return SlideInPrimitive(
                    animation.duration,
                    animation.delay,
                    self._build_transformer(animation.transformer),
                    animation.direction,
                    animation.distance,
                    animation.overshoot
                )
            case "fade_in_primitive":
                return FadeInPrimitive(
                    animation.duration,
                    animation.delay,
                    self._build_transformer(animation.transformer)
                )
            case _:
                raise ValueError(f"Invalid animation type: {animation.type}")
            

    def _build_transformer(self, transformer: str) -> Transformer:
        match transformer:
            case "linear":
                return Transformer.LINEAR
            case "ease_in":
                return Transformer.EASE_IN
            case "ease_out":
                return Transformer.EASE_OUT
            case "ease_in_out":
                return Transformer.EASE_IN_OUT
            case "inverse":
                return Transformer.INVERT
            case _:
                raise ValueError(f"Invalid transformer: {transformer}")

    def _load_semantic_tagger(self) -> None:
        tagger = SemanticTagger()
        for rule in self._config.tagger_rules:
            if rule.type == "ai":
                tagger.add_ai_rule(Tag(rule.tag), rule.prompt)
            elif rule.type == "regex":
                tagger.add_regex_rule(Tag(rule.tag), rule.regex)
            elif rule.type == "wordlist":
                wordlist = open(os.path.join(self._base_path, rule.filename), "r", encoding="utf-8").read().split()
                tagger.add_wordlist_rule(Tag(rule.tag), wordlist)

        self._builder.with_semantic_tagger(tagger)

