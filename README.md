# pycaps

[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/francozanardi/pycaps)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/downloads/)
[![Hugging Face Spaces](https://img.shields.io/badge/Try%20it%20online-Hugging%20Face-blue?logo=huggingface)](https://huggingface.co/spaces/francozanardi/pycaps-new)


**pycaps** is a Python tool for adding CSS styled subtitles to videos. It's designed as both a programmable library and a command-line interface (CLI), making it perfect for automating the creation of dynamic content for platforms like TikTok, YouTube Shorts, and Instagram Reels.

![demo-1](https://github.com/user-attachments/assets/fd2d3325-c986-4b6a-81ba-09c428577e61)
![demo-2](https://github.com/user-attachments/assets/9a789244-0387-4ac8-ab51-b3601447953e)

<sub>See more examples on <a href="https://www.pycaps.com/">pycaps.com</a></sub>

## Try It Online (no installation needed!)

You have two options to test `pycaps` directly in your browser. Choose the one that best fits your needs.

### 1. Interactive Web Demo (on Hugging Face)

Ideal for a **quick preview**, testing built-in templates, and **editing captions** with a user-friendly interface.

[![Hugging Face Spaces](https://img.shields.io/badge/Launch%20Web%20Demo-Hugging%20Face-blue?logo=huggingface)](https://huggingface.co/spaces/francozanardi/pycaps-new)

> **Keep in mind:**
> *   This demo runs on a shared, CPU-only environment, so it's best for **short videos (< 60 seconds)**.
> *   For a private, faster experience, you can **[duplicate the Space](https://huggingface.co/spaces/francozanardi/pycaps-new?duplicate=true)** for free.

### 2. Full-Power Notebook (on Google Colab)

The best choice for **processing longer videos** with **maximum transcription quality**, using a free GPU provided by Google.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/117g6xujecjLyXHBwhwyzx0innCMLh_nj?usp=sharing)

> **Keep in mind:**
> *   The interface is a step-by-step code notebook, not a graphical UI.
> *   You will be guided to enable the GPU for the best performance.

## Key Features

*   **Template System**: Get started quickly with predefined templates. Create and share your own templates, packaging styles, animations, and configurations.
*   **CSS Styling**: Style subtitles using standard CSS. Target specific states like `.word-being-narrated` for dynamic effects, cleanly separating style from logic.
*   **Word Tagging**: Tag words or phrases using regular expressions, word lists, or AI. These tags act as powerful selectors for applying custom CSS, effects, or animations.
*   **Advanced Animations & Effects**: Bring words to life with a library of built-in animations (fades, pops, slides) and effects (typewriting, emoji insertion, sound effects).
*   **Whisper-based Transcription**: Automatically generate accurate, word-level timestamps for your videos using OpenAI's Whisper.
*   **Dual Interface**: Use it as a simple CLI for quick renders or as a comprehensive Python library for programmatic video creation.
*   **Offline-First**: The core transcription, styling, and rendering engine runs entirely on your local machine. An internet connection is only needed for optional AI-powered features that require contextual understanding of your script.

## Prerequisites

Before installing, please ensure your environment meets the following requirements:

*   **Python Version**: `pycaps` was tested on **Python 3.10, 3.11, and 3.12**. Other versions may present issues.

*   **FFmpeg**: You need to have FFmpeg installed on your system and accessible from your command line's `PATH`. This is essential for all audio and video processing tasks.
    *   You can download it from [ffmpeg.org](https://ffmpeg.org/download.html) and follow a guide to add it to your system's `PATH`.

## Installation

pycaps is currently in a very alpha stage and is not yet available on PyPI. You can install it directly from the GitHub repository.

1.  **Install FFmpeg**: Ensure you have completed the prerequisite step above.

2.  **Install pycaps from GitHub:**

    **Full installation (recommended):**
    ```bash
    pip install "git+https://github.com/francozanardi/pycaps.git#egg=pycaps[all]"
    ```

    **Custom installation with specific features:**
    ```bash
    # Basic dependencies to work with default configuration (includes whisper and playwright)
    pip install "git+https://github.com/francozanardi/pycaps.git#egg=pycaps[base]"

    # Faster alternative, doesn't include subtitles editor, and renders without a browser (it uses google cloud speech to text and html2pic to render the subtitles)
    pip install "git+https://github.com/francozanardi/pycaps.git#egg=pycaps[browser]"
    ```

3.  **Install Browser Dependencies for Rendering (Optional):**
    `pycaps` currently has two different options to render the subtitle images:
    - `CssSubtitleRenderer`, which is the original and default one. It uses Playwright to render CSS styles. So, you need to install its browser dependency to use it:
      ```bash
      playwright install chromium
      ```
    - `PictexSubtitleRenderer`, which is a light-weight option. It doesn't use a browser, but it only support a subset of CSS, and it may present some visual differences in the result (specially in the shadows, you should modify the CSS from the templates to get the same results). To use it, you must call `with_custom_subtitle_renderer(PictexSubtitleRenderer())` when `CapsPipelineBuilder()` is created.

> ⚠️ **Note**: The first time you use `pycaps`, it will also download a Whisper AI model for transcription. This may take a few minutes and only happens once.

## Quick Start

There are two primary ways to use pycaps: via the command line with a template or programmatically in a Python script.

### 1. Using the Command-Line (CLI)

The fastest way to get started is to use a built-in template.

```bash
pycaps render --input my_video.mp4 --template minimalist
```

This command will:
1.  Load the `minimalist` template.
2.  Transcribe the audio from `my_video.mp4`.
3.  Apply the template's styles and animations.
4.  Save the result in a new file.

If you already have a transcript from another tool, you can skip built-in transcription:

```bash
pycaps render --input my_video.mp4 --template minimalist --transcript transcript.json
```

Supported transcript formats: `whisper_json`, `pycaps_json`, `srt`, `vtt` (`--transcript-format` is optional and defaults to `auto`).

### 2. Using the Python Library

For full control, use the `CapsPipelineBuilder` in your Python code.

```python
from pycaps import CapsPipelineBuilder

# The pipeline contains multiples stages to render the final video
pipeline = (
    CapsPipelineBuilder()
    .with_input_video("input.mp4")
    .add_css("css_file.css")
    .build()
)
pipeline.run() # When this is executed, it starts to render the video
```

You can also preload the builder using a Template.
```python
from pycaps import *

# Load a template and configure it
builder = TemplateLoader("default").with_input_video("my_video.mp4").load(False)

# Programmatically add an animation
builder.add_animation(
    animation=FadeIn(),
    when=EventType.ON_NARRATION_STARTS,
    what=ElementType.SEGMENT
)

# Build and run the pipeline
pipeline = builder.build()
pipeline.run()
```

## What's Next?

*   🚀 **For Command-Line Users**: Check the **[CLI Usage Guide](./docs/CLI.md)** for a quick and easy start.
*   🧠 **For Developers**: Understand the core concepts in the **[Structure Guide](./docs/CORE_STRUCTURE.md)**.
*   🏷️ **Styling & Logic**: Learn about the powerful **[Tagging System](./docs/TAGS.md)**.
*   🎨 **Reusable Styles**: See how **[Templates](./docs/TEMPLATES.md)** work and how to create your own.
*   💡 **Inspiration**: Dive into **[Code & JSON Examples](./docs/EXAMPLES.md)**.
*   🔧 **Advanced Config**: See all options in the **[JSON Configuration Reference](./docs/CONFIG_REFERENCE.md)**.
*   🤖 **AI Features**: Learn about AI-powered features in the **[API Usage Guide](./docs/API_USAGE.md)**.

## Contributing

This project is in active development. Contributions, bug reports, and feature requests are welcome! Please open an issue or pull request on our [GitHub repository](https://github.com/francozanardi/pycaps).

## License

pycaps is licensed under the [MIT License](https://opensource.org/licenses/MIT).
