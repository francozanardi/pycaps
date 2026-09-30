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
| `quality` | `string` | `middle`| Output video quality. Options: `low`, `middle`, `high`, `veryhigh`. |

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
*   **`split_into_sentences`**:
    *   `"type": "split_into_sentences"`
    *   `"sentences_separators": array[string]` (e.g., `[".", "?", "!"]`)

---

### Effects

`"effects": [ ... ]`

*   **`emoji_in_segment`**: Adds a relevant emoji for a segment. **(Requires API Key)**
    *   `"type": "emoji_in_segment"`
    *   `"chance_to_apply": float` (0.0 to 1.0)
    *   `"align": string` (`top`, `bottom`, `random`)
*   **`emoji_in_word`**: Appends an emoji to words matching a tag.
    *   `"type": "emoji_in_word"`
    *   `"emojis": array[string]` (e.g., `["🔥", "🚀"]`)
    *   `"tag_condition": string` (e.g., `"highlight"`)
*   **`typewriting`**: Renders words character by character.
    *   `"type": "typewriting"`
    *   `"tag_condition": string` (e.g., `"first-line-in-segment"`)
*   **`animate_segment_emojis`**: Replaces static emojis (from `emoji_in_segment`) with animated versions if available.
    *   `"type": "animate_segment_emojis"`
*   **`remove_punctuation_marks`**:
    *   `"type": "remove_punctuation_marks"`
    *   `"punctuation_marks": array[string]`
    *   `"exception_marks": array[string]`

---

### Sound Effects

`"sound_effects": [ ... ]`

| Key            | Description                                                                   |
| -------------- | ----------------------------------------------------------------------------- |
| `type`         | `preset` or `custom`.                                                         |
| `name`         | (For `preset`) e.g., `pop`, `swoosh`, `whoosh`, `click`.                       |
| `path`         | (For `custom`) Path to audio file.                                            |
| `when`         | `narration-starts` or `narration-ends`.                                       |
| `what`         | `word`, `line`, or `segment`.                                                 |
| `tag_condition`| (Optional) Condition for triggering the effect, e.g., `"first-word-in-line"`. |
| `offset`       | (Optional) Time offset in seconds.                                            |
| `volume`       | (Optional) Volume (0.0 to 1.0).                                   |

---

### Animations

`"animations": [ ... ]`

Each object in the array defines an animation.

**Common Properties:**
| Key            | Description                                                                    |
| -------------- | ------------------------------------------------------------------------------ |
| `type`         | Animation name (see list below).                                               |
| `when`         | `narration-starts` or `narration-ends`.                                        |
| `what`         | `word`, `line`, or `segment`.                                                  |
| `tag_condition`| (Optional) Condition for triggering the animation, e.g., `"last-word"`.        |
| `duration`     | Duration in seconds.                                                           |
| `delay`        | (Optional) Delay in seconds.                                                   |

**Animation Types (`type`)**:
*   **preset**: `fade_in`, `fade_out`, `zoom_in`, `zoom_out`, `pop_in`, `pop_out`, `pop_in_bounce`, `slide_in`, `slide_out`.
*   **primitive**: More granular control.
    *   `fade_in_primitive`, `pop_in_primitive`, `zoom_in_primitive`, `slide_in_primitive`.
    *   Can include extra properties like `init_scale`, `overshoot`, and `transformer` (`linear`, `ease_in`, `ease_out`, `inverse`).

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