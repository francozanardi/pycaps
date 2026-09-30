# Configuration Reference (`pycaps.template.json`)

The `pycaps.template.json` file is the heart of a template, defining the entire rendering pipeline. This document serves as a reference for all available options.

## Top-Level Properties

| Key             | Type     | Description                                                                  |
| --------------- | -------- | ---------------------------------------------------------------------------- |
| `input`         | `string` | (Optional) Path to the input video, relative to the config file.             |
| `output`        | `string` | (Optional) Path for the output video.                                        |
| `css`           | `string` | Path to the main CSS stylesheet file, relative to the config file.           |
| `resources`     | `string` | Path to the resources directory (for fonts, images), relative to config.     |
| `video`         | `object` | Video output settings. See [Video Config](#video-config).                    |
| `whisper`       | `object` | Whisper transcription settings. See [Whisper Config](#whisper-config).       |
| `layout`        | `object` | Subtitle layout and positioning. See [Layout Config](#layout-config).          |
| `splitters`     | `array`  | Rules for splitting transcribed text into segments. See [Splitters](#splitters). |
| `effects`       | `array`  | Visual or text-based effects. See [Effects](#effects).                       |
| `sound_effects` | `array`  | Audio effects triggered by events. See [Sound Effects](#sound-effects).        |
| `animations`    | `array`  | Animations for subtitle elements. See [Animations](#animations).             |
| `tagger_rules`  | `array`  | Rules for semantically tagging words. See [Tagger Rules](#tagger-rules).     |
| `cache_strategy`| `string` | Word rendering cache strategy. `css-classes-aware` (default), `position-aware`, `none`. |

---

### Video Config

`"video": { ... }`

| Key       | Type     | Default | Description                                                        |
| --------- | -------- | ------- | ------------------------------------------------------------------ |
| `quality` | `string` | `middle`| Output video quality. Options: `low`, `middle`, `high`, `very_high`. |

---

### Whisper Config

`"whisper": { ... }`

| Key        | Type     | Default | Description                                                                |
| ---------- | -------- | ------- | -------------------------------------------------------------------------- |
| `language` | `string` | `null`  | Language of the audio (e.g., "en", "es"). Auto-detects if `null`.          |
| `model`    | `string` | `base`  | Whisper model size. Options: `tiny`, `base`, `small`, `medium`, `large`. |
| `backend`  | `string` | `openai` | Whisper implementation. Options: `openai` ([openai-whisper](https://github.com/openai/whisper)), `faster` ([faster-whisper](https://github.com/SYSTRAN/faster-whisper), needs to be installed). |

---

### Layout Config

`"layout": { ... }` (Corresponds to `SubtitleLayoutOptions`)

| Key                             | Type     | Default      | Description                                                                              |
| ------------------------------- | -------- | ------------ | ---------------------------------------------------------------------------------------- |
| `x_words_space`                 | `integer`| `0`          | Horizontal space (px) between words. Prefer CSS `margin`.                                |
| `y_words_space`                 | `integer`| `0`          | Vertical space (px) between lines.                                                       |
| `max_width_ratio`               | `float`  | `0.8`        | Maximum width of a line as a ratio of video width (0.0 to 1.0).                          |
| `max_number_of_lines`           | `integer`| `2`          | Maximum number of lines per subtitle segment.                                            |
| `min_number_of_lines`           | `integer`| `1`          | Minimum number of lines per subtitle segment.                                            |
| `on_text_overflow_strategy`     | `string` | `exceed_lines` | How to handle overflow. `exceed_lines` or `exceed_width`.                                |
| `vertical_align`                | `object` | `{...}`      | Vertical alignment settings.                                                             |
| `vertical_align.align`          | `string` | `bottom`     | `top`, `center`, or `bottom`.                                                            |
| `vertical_align.offset`         | `float`  | `0.0`        | Nudges alignment. From `-1.0` (top) to `1.0` (bottom).                                   |

---

### Splitters

`"splitters": [ ... ]`

Array of objects, each defining a splitting rule. They are applied in order.

*   **`limit_by_words`**:
    *   `"type": "limit_by_words"`
    *   `"limit": integer` (e.g., `10`)
*   **`limit_by_chars`**:
    *   `"type": "limit_by_chars"`
    *   `"max_chars": integer` (e.g., `35`)
    *   `"min_chars": integer` (e.g., `15`)
    *   `"avoid_finishing_segment_with_word_shorter_than": integer` (default `0`, disabled). If the last word of a segment is shorter than this, the next words are added to the segment, to avoid finishing it in an unnatural way (e.g., with "a" or "the").
*   **`split_into_sentences`**:
    *   `"type": "split_into_sentences"`
    *   `"sentences_separators": array[string]` (e.g., `[".", "?", "!"]`)

---

### Effects

`"effects": [ ... ]`

Array of effects, applied in order. For a step-by-step explanation with examples, see the [Effects & Animations Guide](./EFFECTS_AND_ANIMATIONS.md#7-built-in-effects).

| `type` | Options (default) |
| --- | --- |
| `remove_punctuation_marks` | `punctuation_marks` (`["."]`), `exception_marks` (`["..."]`) |
| `emoji_in_word` | `emojis` (required), `tag_condition` (`""`), `avoid_use_same_emoji_in_a_row` (`true`) |
| `emoji_in_segment` **(Requires API Key)** | `chance_to_apply` (`0.5`), `align` (`random`: `top`, `bottom` or `random`), `ignore_segments_with_duration_less_than` (`0`), `max_uses_of_each_emoji` (`2`), `max_consecutive_segments_with_emoji` (`3`) |
| `typewriting` | `tag_condition` (`""`) |
| `animate_segment_emojis` | No options. Must be used after `emoji_in_segment`. |

---

### Sound Effects

`"sound_effects": [ ... ]`

See the [Effects & Animations Guide](./EFFECTS_AND_ANIMATIONS.md#8-sound-effects) for examples.

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `type` | `string` | (required) | `preset` or `custom`. |
| `name` | `string` | (required for `preset`) | `click`, `click-light`, `ding`, `ding-long`, `ding-short`, `glitch`, `glitch-static`, `heart-beat`, `hit-intense`, `hit-strong`, `pop`, `pop-2`, `slide-paper`, `swoosh`, `whoosh`, `whoosh-2` or `whoosh-deep`. |
| `path` | `string` | (required for `custom`) | Path to an audio file, relative to the config file. |
| `when` | `string` | (required) | `narration-starts` or `narration-ends`. |
| `what` | `string` | (required) | `word`, `line` or `segment`. |
| `tag_condition` | `string` | `""` | Condition for triggering the sound, e.g., `"first-word-in-line"`. |
| `offset` | `float` | `0.0` | Time offset in seconds. |
| `volume` | `float` | `0.25` | Volume, from `0.0` to `1.0`. |
| `interpret_consecutive_words_as_one` | `boolean` | `true` | With `what: word`, consecutive words matching `tag_condition` play the sound only once. |

---

### Animations

`"animations": [ ... ]`

Each object in the array defines an animation. For a step-by-step explanation with examples, see the [Effects & Animations Guide](./EFFECTS_AND_ANIMATIONS.md).

**Common Properties:**

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `type` | `string` | (required) | Animation name (see below). |
| `when` | `string` | (required) | `narration-starts` or `narration-ends`. |
| `what` | `string` | (required) | `word`, `line` or `segment`. |
| `tag_condition` | `string` | `""` | Condition for triggering the animation, e.g., `"last-word-in-line"`. |
| `duration` | `float` | `0.2` | Duration in seconds. |
| `delay` | `float` | `0.0` | Delay in seconds. |

**Presets:**

| `type` | Extra options (default) |
| --- | --- |
| `fade_in`, `fade_out`, `zoom_in`, `zoom_out`, `pop_in`, `pop_out`, `pop_in_bounce` | |
| `slide_in`, `slide_out` | `direction` (`left` for `slide_in`, `right` for `slide_out`): `left`, `right`, `up` or `down` |

**Primitives:**

All primitives also accept `transformer` (`linear`): `linear`, `ease_in`, `ease_out`, `ease_in_out` or `inverse`.

| `type` | Extra options (default) |
| --- | --- |
| `fade_in_primitive` | |
| `zoom_in_primitive` | `init_scale` (`0.5`), `overshoot` |
| `pop_in_primitive` | `init_scale` (`0.7`), `min_scale` (`0.3`), `min_scale_at` (`0.5`), `overshoot` |
| `slide_in_primitive` | `direction` (`left`), `distance` (`100`), `overshoot` |

`overshoot` is an object with `amount` (`0.1`) and `peak_at` (`0.7`), e.g., `"overshoot": { "amount": 0.1, "peak_at": 0.7 }`. If it's not set, there's no overshoot.

---

### Tagger Rules

`"tagger_rules": [ ... ]`

Define rules to add semantic tags to words.

*   **`ai`**: Uses an LLM to tag words based on a prompt. **(Requires API Key)**
    *   `"type": "ai"`
    *   `"tag": string` (The tag to apply, e.g., `"financial_term"`)
    *   `"prompt": string` (The concept to look for, e.g., `"words related to money or finance"`)
*   **`regex`**: Uses a regular expression.
    *   `"type": "regex"`
    *   `"tag": string`
    *   `"regex": string` (e.g., `"\$\d+"`)
*   **`wordlist`**: Matches words from a file.
    *   `"type": "wordlist"`
    *   `"tag": string`
    *   `"filename": string` (Path to a text file with one word per line, relative to config).