# Effects & Animations Guide

This guide explains how to bring your subtitles to life. It starts with the basics and builds up step by step, so if you're new to `pycaps`, read it in order. If you're looking for a specific option, jump to the [catalog of animations](#5-built-in-animations) or the [catalog of effects](#7-built-in-effects).

Every example is shown in two ways, since they are equivalent:

- **JSON**: inside a template's `pycaps.template.json` (or a `--config` file). See the [Templates Guide](./TEMPLATES.md).
- **Python**: using the `CapsPipelineBuilder`.

## Table of Contents

1. [Styles, effects and animations: what's the difference?](#1-styles-effects-and-animations-whats-the-difference)
2. [Your first animation](#2-your-first-animation)
3. [Timing: `when`, `what`, `duration` and `delay`](#3-timing-when-what-duration-and-delay)
4. [Targeting specific words with `tag_condition`](#4-targeting-specific-words-with-tag_condition)
5. [Built-in animations](#5-built-in-animations)
6. [Combining animations](#6-combining-animations)
7. [Built-in effects](#7-built-in-effects)
8. [Sound effects](#8-sound-effects)
9. [Creating your own effects and animations](#9-creating-your-own-effects-and-animations)

---

## 1. Styles, effects and animations: what's the difference?

`pycaps` splits the look of your subtitles into three independent parts:

| | What it controls | Example |
| --- | --- | --- |
| **Styles (CSS)** | How each word looks: font, color, size, background, shadows. | The word being spoken is yellow. |
| **Effects** | What is shown: they change the text or the rendered words. | Remove the trailing periods, add an emoji, write each word letter by letter. |
| **Animations** | How words move over time: they fade, scale or move them. | Each segment fades in when it starts. |

To understand when effects and animations are applied, it helps to know the steps of the pipeline:

1. **Transcription**: the audio is transcribed into a `Document` made of segments, lines and words (see [Core Concepts](./CORE_STRUCTURE.md)).
2. **Tagging**: words, lines and segments get tags, like `first-word-in-line` or your own `highlight` (see [Tagging System](./TAGS.md)).
3. **Text effects** run: they can modify the text of the words.
4. **Rendering**: each word is rendered to images using your CSS, one image for each state (not narrated yet, being narrated, already narrated).
5. **Clip effects** and **sound effects** run: they can replace the rendered images or add sounds.
6. **Animations** run: they change the position, size and opacity of the rendered images over time.

You don't need to remember all of this now, but it explains some behaviors later. For example, text effects run before rendering, so if an effect adds an emoji to a word, the layout already takes that emoji into account.

---

## 2. Your first animation

Let's make each subtitle segment fade in when it starts and fade out when it ends. This is exactly what the built-in `default` template does.

**JSON**
```json
{
  "css": "styles.css",
  "animations": [
    { "type": "fade_in", "when": "narration-starts", "what": "segment" },
    { "type": "fade_out", "when": "narration-ends", "what": "segment" }
  ]
}
```

**Python**
```python
from pycaps import *

builder = CapsPipelineBuilder()
builder.with_input_video("my_video.mp4")
builder.add_css("styles.css")

builder.add_animation(FadeIn(), when=EventType.ON_NARRATION_STARTS, what=ElementType.SEGMENT)
builder.add_animation(FadeOut(), when=EventType.ON_NARRATION_ENDS, what=ElementType.SEGMENT)

builder.build().run()
```

Every animation needs three things:

- **`type`**: which animation to run (`fade_in`). In Python, it's the animation class (`FadeIn()`).
- **`when`**: the moment that triggers it: when the narration starts or when it ends.
- **`what`**: the element whose narration triggers it: a `word`, a `line` or a `segment`.

So the first animation reads as: *"fade in when the narration of each segment starts"*.

> **Tip:** You can also add animations on top of a template from Python:
> ```python
> builder = TemplateLoader("minimalist").with_input_video("my_video.mp4").load(False)
> builder.add_animation(PopIn(), when=EventType.ON_NARRATION_STARTS, what=ElementType.WORD)
> builder.build().run()
> ```

---

## 3. Timing: `when`, `what`, `duration` and `delay`

### `what`: the element that triggers the animation

The same animation looks very different depending on `what`:

- **`segment`**: the whole segment is animated at once, when the segment starts (or ends) being spoken.
- **`line`**: each line is animated when that line starts (or ends) being spoken.
- **`word`**: each word is animated when that word starts (or ends) being spoken.

For example, `{"type": "pop_in", "when": "narration-starts", "what": "word"}` makes each word pop in as it's being said, while `"what": "segment"` pops the whole segment in at once.

`what` also defines the center used by the animations that scale (`zoom_*` and `pop_*`): a segment grows from the center of the segment, and a word from the center of the word.

### `when`: at the start or at the end

- **`narration-starts`**: the animation **starts** when the element starts being spoken.
- **`narration-ends`**: the animation **finishes** when the element stops being spoken.

That's why "in" animations (`fade_in`, `pop_in`, ...) are normally used with `narration-starts`, and "out" animations (`fade_out`, `pop_out`, ...) with `narration-ends`:

```
segment narration:   |-------- "like my phone went from" --------|
fade_in  (starts)    |===|
fade_out (ends)                                             |===|
```

### `duration` and `delay`

- **`duration`**: how long the animation lasts, in seconds.
- **`delay`**: moves the animation away from the moment it's attached to, in seconds. With `narration-starts`, the animation starts `delay` seconds **later**. With `narration-ends`, it finishes `delay` seconds **earlier**.

**JSON**
```json
{ "type": "fade_in", "when": "narration-starts", "what": "segment", "duration": 0.4, "delay": 0.1 }
```

**Python**
```python
builder.add_animation(FadeIn(duration=0.4, delay=0.1), when=EventType.ON_NARRATION_STARTS, what=ElementType.SEGMENT)
```

> **Note about the default durations:** in JSON, every animation lasts `0.2` seconds unless you set `duration`. In Python, each class has its own default (for example, `PopIn()` lasts `0.3` seconds). The tables in [section 5](#5-built-in-animations) list them.

---

## 4. Targeting specific words with `tag_condition`

By default, an animation applies to every element. With `tag_condition`, you can restrict it to the words that have (or don't have) certain tags. Tags come from two places:

- **Structure tags**, added automatically depending on the position: `first-word-in-line`, `last-line-in-segment`, etc.
- **Semantic tags**, added by your own rules: for example, a `highlight` tag for important words.

The full list of tags and how to create your own rules are explained in the [Tagging System](./TAGS.md). Conditions support `and`, `or`, `not` and parentheses.

**Example: make only the highlighted words zoom in.**

**JSON**
```json
{
  "tagger_rules": [
    { "type": "wordlist", "tag": "highlight", "filename": "highlight_words.txt" }
  ],
  "animations": [
    { "type": "zoom_in", "when": "narration-starts", "what": "word", "tag_condition": "highlight" }
  ]
}
```

**Python**
```python
tagger = SemanticTagger()
tagger.add_wordlist_rule(Tag("highlight"), ["amazing", "free", "now"])
builder.with_semantic_tagger(tagger)

builder.add_animation(
    ZoomIn(),
    when=EventType.ON_NARRATION_STARTS,
    what=ElementType.WORD,
    tag_condition=TagConditionFactory.parse("highlight"),
)
```

A condition always checks the tags of each **word**, together with the structure tags of its line and its segment. That's why you can also use line or segment tags to target words:

```json
{ "type": "slide_in", "when": "narration-starts", "what": "line", "direction": "left", "tag_condition": "first-line-in-segment" }
```

In Python, you can build the same conditions with `TagConditionFactory`:

```python
# These two conditions are equivalent
condition = TagConditionFactory.parse("highlight and not first-word-in-line")
condition = TagConditionFactory.AND(
    TagConditionFactory.HAS(Tag("highlight")),
    TagConditionFactory.NOT(BuiltinTag.FIRST_WORD_IN_LINE),
)
```

---

## 5. Built-in animations

There are two kinds of built-in animations:

- **Presets**: ready-to-use animations with a nice default look. Start with these.
- **Primitives**: the building blocks used by the presets. Use them when you need more control (initial size, distance, easing, etc.).

### Presets

All presets accept `duration` and `delay` (see [section 3](#3-timing-when-what-duration-and-delay)).

| JSON `type` | Python class | What it does | Python default `duration` | Extra options |
| --- | --- | --- | --- | --- |
| `fade_in` | `FadeIn` | Fades in from transparent. | `0.2` | |
| `fade_out` | `FadeOut` | Fades out to transparent. | `0.2` | |
| `pop_in` | `PopIn` | Grows from half its size with a small bounce, while fading in. | `0.3` | |
| `pop_out` | `PopOut` | Shrinks while fading out. | `0.2` | |
| `pop_in_bounce` | `PopInBounce` | Like `pop_in`, but shrinks first and then bounces, for a more playful effect. | `0.4` | |
| `zoom_in` | `ZoomIn` | Grows from half its size with a small overshoot, while fading in. | `0.3` | |
| `zoom_out` | `ZoomOut` | Shrinks while fading out. | `0.3` | |
| `slide_in` | `SlideIn` | Slides in from a side, while fading in. | `0.3` | `direction` (default `left`) |
| `slide_out` | `SlideOut` | Slides out to a side, while fading out. | `0.3` | `direction` (default `right`) |

Remember that in JSON the default `duration` is always `0.2`.

For `slide_in`, `direction` is the side the element **comes from**. For `slide_out`, it's the side it **goes to**. The options are `left`, `right`, `up` and `down`.

**JSON**
```json
{ "type": "slide_in", "when": "narration-starts", "what": "segment", "direction": "up", "duration": 0.3 }
```

**Python**
```python
builder.add_animation(SlideIn(direction=Direction.UP, duration=0.3), when=EventType.ON_NARRATION_STARTS, what=ElementType.SEGMENT)
```

### Primitives

Each primitive changes a single thing (opacity, size or position), and all of them are "in" animations. They accept these common options:

| Option | Default | Description |
| --- | --- | --- |
| `duration` | `0.2` (JSON) | Duration in seconds. **Required** in Python. |
| `delay` | `0.0` | Delay in seconds. |
| `transformer` | `linear` | Easing function. See [Transformers](#transformers-easing). |

And these specific ones:

| JSON `type` | Python class | What it does | Extra options |
| --- | --- | --- | --- |
| `fade_in_primitive` | `FadeInPrimitive` | Changes the opacity from 0 to 1. | |
| `zoom_in_primitive` | `ZoomInPrimitive` | Scales from `init_scale` to the final size. | `init_scale` (`0.5`), `overshoot` |
| `pop_in_primitive` | `PopInPrimitive` | Scales from `init_scale` down to `min_scale`, and then up to the final size. | `init_scale` (`0.7`), `min_scale` (`0.3`), `min_scale_at` (`0.5`), `overshoot` |
| `slide_in_primitive` | `SlideInPrimitive` | Moves from `distance` pixels away to the final position. | `direction` (`left`), `distance` (`100`), `overshoot` |

`min_scale_at` is the moment (from `0.0` to `1.0` of the animation) when `pop_in_primitive` reaches `min_scale`. It must be lower than `overshoot.peak_at`.

Since primitives change a single thing, they're commonly combined. For example, the built-in `explosive` template makes each word grow quickly with a small overshoot:

**JSON**
```json
{
  "type": "zoom_in_primitive",
  "when": "narration-starts",
  "what": "word",
  "duration": 0.2,
  "init_scale": 0.5,
  "overshoot": { "amount": 0.1, "peak_at": 0.7 }
}
```

**Python**
```python
builder.add_animation(
    ZoomInPrimitive(duration=0.2, init_scale=0.5, overshoot=OvershootConfig(amount=0.1, peak_at=0.7)),
    when=EventType.ON_NARRATION_STARTS,
    what=ElementType.WORD,
)
```

#### Overshoot

`overshoot` makes the animation go a bit further than the final value and then come back, which feels more natural. It has two options:

- **`amount`** (default `0.1`): how far it goes past the final value. For scale animations, `0.1` means 10% bigger than the final size. For `slide_in_primitive`, it's a fraction of `distance`.
- **`peak_at`** (default `0.7`): the moment (from `0.0` to `1.0` of the animation) when it reaches that maximum.

Without `overshoot`, the animation goes straight to the final value.

#### Transformers (easing)

A transformer changes the speed of the animation over time:

| JSON value | Python value | Description |
| --- | --- | --- |
| `linear` | `Transformer.LINEAR` | Constant speed. |
| `ease_in` | `Transformer.EASE_IN` | Starts slow and speeds up. |
| `ease_out` | `Transformer.EASE_OUT` | Starts fast and slows down. Good for elements that enter the screen. |
| `ease_in_out` | `Transformer.EASE_IN_OUT` | Starts and ends slow. |
| `inverse` | `Transformer.INVERT` | Plays the animation backwards. |

`inverse` is how "out" animations are built from primitives: a `fade_in_primitive` with the `inverse` transformer fades out. For example, the built-in `retro-gaming` template slides each segment in from above, and then slides it out downwards:

```json
"animations": [
  { "type": "slide_in_primitive", "when": "narration-starts", "what": "segment", "duration": 0.3, "direction": "up", "distance": 50, "transformer": "ease_out" },
  { "type": "slide_out", "when": "narration-ends", "what": "segment", "duration": 0.3, "direction": "down" }
]
```

---

## 6. Combining animations

You can add as many animations as you want, and they are applied in order. A common pattern is to animate the segment and the words at the same time. For example, the built-in `hype` template fades each segment in and out, and makes each word grow when it's spoken:

**JSON**
```json
"animations": [
  { "type": "zoom_in_primitive", "when": "narration-starts", "what": "word", "duration": 0.12, "init_scale": 0.8, "overshoot": { "amount": 0.05, "peak_at": 0.7 } },
  { "type": "fade_in", "when": "narration-starts", "what": "segment", "duration": 0.15 },
  { "type": "fade_out", "when": "narration-ends", "what": "segment", "duration": 0.15 }
]
```

**Python**
```python
builder.add_animation(
    ZoomInPrimitive(duration=0.12, init_scale=0.8, overshoot=OvershootConfig(amount=0.05, peak_at=0.7)),
    when=EventType.ON_NARRATION_STARTS,
    what=ElementType.WORD,
)
builder.add_animation(FadeIn(duration=0.15), when=EventType.ON_NARRATION_STARTS, what=ElementType.SEGMENT)
builder.add_animation(FadeOut(duration=0.15), when=EventType.ON_NARRATION_ENDS, what=ElementType.SEGMENT)
```

Keep in mind that if two animations change the same property (for example, the opacity) of the same word at the same time, the last one added wins.

---

## 7. Built-in effects

Effects go in the `effects` array of the JSON, or are added with `builder.add_effect(...)` in Python. Sound effects are a special kind of effect, explained in [section 8](#8-sound-effects).

### Text effects

These effects modify the words before rendering.

#### `remove_punctuation_marks`

Removes punctuation marks from the words, except the ones listed as exceptions.

| Option | Default | Description |
| --- | --- | --- |
| `punctuation_marks` | `["."]` | Marks to remove. |
| `exception_marks` | `["..."]` | Marks to keep, even if they contain a mark to remove. |

**JSON**
```json
{ "type": "remove_punctuation_marks", "punctuation_marks": [".", ","], "exception_marks": ["..."] }
```

**Python**
```python
builder.add_effect(RemovePunctuationMarksEffect(punctuation_marks=[".", ","], exception_marks=["..."]))
```

#### `emoji_in_word`

Adds a random emoji from a list after the words that match a tag condition. If several consecutive words match, the emoji is added only once, after the last one.

| Option | Default | Description |
| --- | --- | --- |
| `emojis` | (required) | List of emojis to choose from. |
| `tag_condition` | `""` | Words that get an emoji. See [section 4](#4-targeting-specific-words-with-tag_condition). |
| `avoid_use_same_emoji_in_a_row` | `true` | Avoids repeating the same emoji twice in a row. |

**JSON**
```json
{ "type": "emoji_in_word", "emojis": ["🔥", "🚀"], "tag_condition": "highlight" }
```

**Python**
```python
builder.add_effect(EmojiInWordEffect(emojis=["🔥", "🚀"], tag_condition=TagConditionFactory.parse("highlight")))
```

#### `emoji_in_segment`

Uses AI to add a relevant emoji to the segments, in a new line above or below the text. **It requires an OpenAI API key**, see [AI Features](./API_USAGE.md). Without one, the effect is skipped with a warning.

| Option | Default | Description |
| --- | --- | --- |
| `chance_to_apply` | `0.5` | Probability (from `0.0` to `1.0`) of adding an emoji to each segment. |
| `align` | `random` | Where to put the emoji: `top`, `bottom` or `random`. |
| `ignore_segments_with_duration_less_than` | `0` | Skips segments shorter than this, in seconds. `0` disables it. |
| `max_uses_of_each_emoji` | `2` | Maximum number of times the same emoji can be used. `0` disables the limit. |
| `max_consecutive_segments_with_emoji` | `3` | Maximum number of consecutive segments with an emoji. `0` disables the limit. |

The emoji is a word with the `emoji-for-segment` tag, so you can style it in CSS:

```css
.word.emoji-for-segment {
  font-size: 48px;
}
```

**JSON**
```json
{ "type": "emoji_in_segment", "chance_to_apply": 0.85, "align": "bottom", "max_uses_of_each_emoji": 1 }
```

**Python**
```python
builder.add_effect(EmojiInSegmentEffect(chance_to_apply=0.85, align=EmojiAlign.BOTTOM, max_uses_of_each_emoji=1))
```

#### Modifying words from Python

`ModifyWordsEffect` runs a function on each word that matches a tag condition (or on every word, if there's no condition). It's only available from Python.

```python
# Wrap the highlighted words with asterisks
builder.add_effect(ModifyWordsEffect(
    modifier=lambda word: setattr(word, "text", f"*{word.text}*"),
    tag_condition=TagConditionFactory.parse("highlight"),
))
```

### Clip effects

These effects modify the rendered words.

#### `typewriting`

Writes each word letter by letter while it's being spoken. It renders an image for each letter, so it makes the render slower.

| Option | Default | Description |
| --- | --- | --- |
| `tag_condition` | `""` | Words that get the effect. By default, all of them. |

**JSON**
```json
{ "type": "typewriting" }
```

**Python**
```python
builder.add_effect(TypewritingEffect())
```

#### `animate_segment_emojis`

Replaces the emojis added by `emoji_in_segment` with animated versions, when available. It has no options, and it must be added after `emoji_in_segment`. The first time, it downloads the animated emojis pack.

**JSON**
```json
"effects": [
  { "type": "emoji_in_segment", "chance_to_apply": 0.85 },
  { "type": "animate_segment_emojis" }
]
```

**Python**
```python
builder.add_effect(EmojiInSegmentEffect(chance_to_apply=0.85))
builder.add_effect(AnimateSegmentEmojisEffect())
```

---

## 8. Sound effects

Sound effects play a sound when an element starts or ends being spoken. They use the same `when`, `what` and `tag_condition` as animations. In JSON, they go in their own `sound_effects` array. In Python, they're added with `add_effect`.

| Option | Default | Description |
| --- | --- | --- |
| `type` | (required, JSON only) | `preset` for a built-in sound, or `custom` for your own file. |
| `name` | (required for `preset`) | Name of the built-in sound (see the list below). |
| `path` | (required for `custom`) | Path to an audio file, relative to the config file. |
| `when` | (required) | `narration-starts` or `narration-ends`. |
| `what` | (required) | `word`, `line` or `segment`. |
| `tag_condition` | `""` | Elements that play the sound. |
| `offset` | `0.0` | Moves the sound, in seconds. Negative values play it earlier. |
| `volume` | `0.25` | Volume, from `0.0` to `1.0`. |
| `interpret_consecutive_words_as_one` | `true` | With `what: word` and a `tag_condition`, a group of consecutive matching words plays the sound only once: on the first word with `narration-starts`, or on the last one with `narration-ends`. |

Built-in sounds: `click`, `click-light`, `ding`, `ding-long`, `ding-short`, `glitch`, `glitch-static`, `heart-beat`, `hit-intense`, `hit-strong`, `pop`, `pop-2`, `slide-paper`, `swoosh`, `whoosh`, `whoosh-2`, `whoosh-deep`.

**Example: play a "ding" when a highlighted word is spoken, and a custom sound when each segment starts.**

**JSON**
```json
"sound_effects": [
  { "type": "preset", "name": "ding", "when": "narration-starts", "what": "word", "tag_condition": "highlight", "volume": 0.2 },
  { "type": "custom", "path": "resources/my-sound.mp3", "when": "narration-starts", "what": "segment" }
]
```

**Python**
```python
builder.add_effect(SoundEffect(
    BuiltinSound.DING,
    when=EventType.ON_NARRATION_STARTS,
    what=ElementType.WORD,
    tag_condition=TagConditionFactory.parse("highlight"),
    volume=0.2,
))
builder.add_effect(SoundEffect(
    Sound("my-sound", "resources/my-sound.mp3"),
    when=EventType.ON_NARRATION_STARTS,
    what=ElementType.SEGMENT,
))
```

---

## 9. Creating your own effects and animations

When the built-in options aren't enough, you can write your own in Python. Custom effects and animations can't be referenced from a JSON file, but you can still load a template and add them on top of it:

```python
builder = TemplateLoader("minimalist").with_input_video("my_video.mp4").load(False)
builder.add_effect(MyEffect())
builder.build().run()
```

### A custom text effect

A text effect is a class that extends `TextEffect` and implements `run(document)`. It receives the whole [`Document`](./CORE_STRUCTURE.md), so it can change anything before rendering. For example, this effect hides some words with asterisks:

```python
from pycaps import *

class CensorEffect(TextEffect):
    def __init__(self, words_to_censor: list[str]):
        self._words_to_censor = {word.lower() for word in words_to_censor}

    def run(self, document: Document) -> None:
        for word in document.get_words():
            if word.text.lower().strip(".,!?") in self._words_to_censor:
                word.text = "*" * len(word.text)

builder.add_effect(CensorEffect(["damn", "heck"]))
```

For simple changes like this one, [`ModifyWordsEffect`](#modifying-words-from-python) is usually enough. Extending `TextEffect` is useful when you need to look at more than one word at a time (for example, the previous or next word).

### A custom animation built from other animations

The easiest way to create an animation is to combine existing ones. Extend `PresetAnimation` and return the animations to combine in `_build_animations()`. For example, a short "rise" effect that moves the element up a few pixels while it fades in:

```python
from pycaps import *

class RiseIn(PresetAnimation):
    def __init__(self, duration: float = 0.3, delay: float = 0.0):
        super().__init__(duration, delay)

    def _build_animations(self) -> list[Animation]:
        return [
            SlideInPrimitive(self._duration, self._delay, Transformer.EASE_OUT, direction=Direction.DOWN, distance=30),
            FadeInPrimitive(self._duration, self._delay),
        ]

builder.add_animation(RiseIn(), when=EventType.ON_NARRATION_STARTS, what=ElementType.LINE)
```

### A custom primitive animation

If you need a completely new movement, extend `PrimitiveAnimation` and implement `_apply_animation(clip, offset)`. Inside it, call one or more of these helpers with a function that receives the progress of the animation `t` (from `0.0` to `1.0`, already transformed by the easing function) and returns the value for that moment:

- `self._apply_opacity(clip, offset, fn)`: `fn(t)` returns the opacity, from `0.0` to `1.0`.
- `self._apply_size(clip, offset, fn)`: `fn(t)` returns the scale, where `1.0` is the original size.
- `self._apply_position(clip, offset, fn)`: `fn(t)` returns the `(x, y)` position in pixels. The final position of the word is in `clip.layout.position`.

For example, a blink effect that turns the element on and off three times:

```python
from pycaps import *

class BlinkPrimitive(PrimitiveAnimation):
    def __init__(self, duration: float = 0.6, delay: float = 0.0, blinks: int = 3):
        super().__init__(duration, delay)
        self._blinks = blinks

    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        self._apply_opacity(clip, offset, lambda t: 1.0 if t >= 1.0 else float(int(t * self._blinks * 2) % 2))

builder.add_animation(
    BlinkPrimitive(),
    when=EventType.ON_NARRATION_STARTS,
    what=ElementType.WORD,
    tag_condition=TagConditionFactory.parse("highlight"),
)
```

The `transformer` argument of `PrimitiveAnimation` is applied automatically, so your custom primitive also supports easing and `Transformer.INVERT` for free.

---

## What's next?

- See all the JSON options in one place in the [Configuration Reference](./CONFIG_REFERENCE.md).
- Learn how to create your own tags in the [Tagging System](./TAGS.md).
- Browse the built-in templates (for example, with `pycaps template create --name my-template --from hype`) to see how they combine styles, effects and animations.
