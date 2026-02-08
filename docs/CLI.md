# CLI Usage Guide

The `pycaps` Command-Line Interface (CLI) is designed for ease of use, allowing you to render videos quickly without writing any Python code.

## Main Commands

The CLI is structured into several commands:

-   `pycaps render`: The main command to process and render a video.
-   `pycaps preview-styles`: A tool to live-preview your CSS styles.
-   `pycaps template`: Commands for managing templates.
-   `pycaps config`: Manage your API key.

You can always get help for any command by adding `--help`, for example: `pycaps render --help`.

## `pycaps render`

This is the command you'll use most often. It takes an input video and generates a new one with subtitles.

### Basic Usage

The simplest way to run it is with an input video and a template.

```bash
pycaps render --input my_video.mp4 --template default
```
This will create a new video named `output_... .mp4` in your current directory.

### Common `render` Options

#### Main Options
-   `--input <path>`: **(Required)** Path to your input video file.
-   `--output <path>`: (Optional) Specify the name of the output file.
-   `--template <name>`: Use a built-in or local template.
-   `--config <path>`: Use a JSON configuration file instead of a template.
-   `--transcription-preview`: **(Very useful!)** This stops the process after transcription and opens a GUI to let you edit the transcribed text and timings.

#### Style & Layout
-   `--style <selector.property=value>`: Override a CSS style on the fly. Can be used multiple times.
    ```bash
    # Example: Make the current word yellow and bigger
    pycaps render ... --style ".word-being-narrated.color=yellow" --style ".word-being-narrated.font-size=72px"
    ```
-   `--layout-align <value>`: Change vertical alignment. Options: `top`, `center`, `bottom`.
-   `--layout-align-offset <value>`: Nudge the vertical alignment. A value from -1.0 (up) to 1.0 (down).

#### Utilities
-   `--preview`: Renders a quick, low-quality preview of the first 5 seconds.
-   `--preview-time <start,end>`: Renders a preview of a specific time range.
    ```bash
    # Preview from 10.5 seconds to 15 seconds
    pycaps render ... --preview-time 10.5,15
    ```
-   `--subtitle-data <path>`: Skips transcription and uses a pre-generated `.json` data file. Great for re-rendering with different styles.
-   `--transcript <path>`: Uses an external transcription input and skips built-in STT.
-   `--transcript-format <auto|whisper_json|pycaps_json|srt|vtt>`: Declares transcript format (defaults to `auto`).
-   `-v`, `--verbose`: Show detailed logs during processing.

### External Transcript Input

If you already transcribed audio with another tool, you can pass that file directly:

```bash
pycaps render --input my_video.mp4 --template minimalist --transcript transcript.json
```

Supported formats:
-   `whisper_json` (Whisper response with `segments[].words[]`)
-   `pycaps_json` (pycaps document JSON or lightweight `segments[].words[]`)
-   `srt`
-   `vtt` (including inline timestamp tags)

Use `--transcript-format` when auto-detection is not enough:

```bash
pycaps render --input my_video.mp4 --template minimalist --transcript subtitles.vtt --transcript-format vtt
```

`--subtitle-data` is different: it expects already processed pycaps subtitle data and skips both transcription and processing. `--transcript` still runs processing (splitters, tags, effects) after loading text/timings.

## `pycaps preview-styles`

This command launches a GUI to help you design your subtitle styles in real-time, without needing a video.

### Usage
You can preview a standalone CSS file or the styles from a template.

```bash
# Preview styles from a CSS file and a resources folder
pycaps preview-styles --css my-styles.css --resources ./fonts

# Or, preview the styles directly from a template
pycaps preview-styles --template my-cool-template
```
This will open a window where you can see how your subtitles look and test different states and tags.

## `pycaps template`

Manage your project templates.

-   `pycaps template list`: Shows all built-in templates and any local templates in your current directory.
-   `pycaps template create --name <name>`: Creates a new template directory by copying a base template.
    ```bash
    # Create a new template called 'my-new-style' based on the 'default' one
    pycaps template create --name my-new-style --from default
    ```

## `pycaps config`

Manage your Pycaps API key for AI features.

-   `pycaps config`: Shows your currently saved API key, if any.
-   `pycaps config --set-api-key <your-key>`: Saves your API key locally.
-   `pycaps config --unset-api-key`: Removes your saved API key.
