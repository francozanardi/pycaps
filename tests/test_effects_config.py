import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from pycaps.common import Document, ElementType, EventType, Line, Segment, Tag, TimeFragment, Word
from pycaps.effect import BuiltinSound, ModifyWordsEffect, SoundEffect
from pycaps.pipeline import JsonConfigLoader
from pycaps.tag import TagConditionFactory


def _make_document(*texts: str) -> Document:
    document = Document()
    time = TimeFragment(start=0.0, end=1.0)
    segment = Segment(time=time)
    line = Line(time=time)
    for text in texts:
        line.words.add(Word(text=text, time=time))
    segment.lines.add(line)
    document.segments.add(segment)
    return document


class ModifyWordsEffectTests(unittest.TestCase):

    def test_modifies_all_words_without_tag_condition(self):
        document = _make_document("hello", "world")
        ModifyWordsEffect(modifier=lambda word: setattr(word, "text", word.text.upper())).run(document)
        self.assertEqual([w.text for w in document.get_words()], ["HELLO", "WORLD"])

    def test_modifies_only_words_matching_tag_condition(self):
        document = _make_document("hello", "world")
        document.get_words()[1].semantic_tags.add(Tag("highlight"))
        ModifyWordsEffect(
            modifier=lambda word: setattr(word, "text", word.text.upper()),
            tag_condition=TagConditionFactory.HAS(Tag("highlight")),
        ).run(document)
        self.assertEqual([w.text for w in document.get_words()], ["hello", "WORLD"])


@patch("pycaps.pipeline.caps_pipeline.check_dependencies", return_value=None)
class SoundEffectsConfigTests(unittest.TestCase):

    def _load_sound_effect(self, sound_effect: dict, sound_file: str = None) -> SoundEffect:
        with tempfile.TemporaryDirectory() as tmp_dir:
            if sound_file:
                shutil.copy(BuiltinSound.POP.get_file_path(), os.path.join(tmp_dir, sound_file))
            config_path = os.path.join(tmp_dir, "pycaps.template.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump({"sound_effects": [sound_effect]}, f)
            builder = JsonConfigLoader(config_path).load(False)
            return builder._caps_pipeline._sound_effects[0], tmp_dir

    def test_preset_sound_effect(self, _mock_dependencies):
        effect, _ = self._load_sound_effect({"type": "preset", "name": "pop", "when": "narration-ends", "what": "line"})
        self.assertEqual(effect._when, EventType.ON_NARRATION_ENDS)
        self.assertEqual(effect._what, ElementType.LINE)

    def test_custom_sound_effect_path_is_relative_to_config(self, _mock_dependencies):
        effect, tmp_dir = self._load_sound_effect(
            {"type": "custom", "path": "my-sound.mp3", "when": "narration-ends", "what": "line"},
            sound_file="my-sound.mp3",
        )
        self.assertEqual(effect._when, EventType.ON_NARRATION_ENDS)
        self.assertEqual(effect._what, ElementType.LINE)
        self.assertEqual(effect._sound.get_file_path(), os.path.join(tmp_dir, "my-sound.mp3"))


if __name__ == "__main__":
    unittest.main()
