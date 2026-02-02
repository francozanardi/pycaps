# pycaps Architecture Overview

This document provides a comprehensive overview of the pycaps codebase architecture for developers and contributors.

## Project Structure

```
pycaps/
├── src/pycaps/           # Main source code
│   ├── __init__.py       # Package exports
│   ├── bootstrap.py      # Dependency checks (FFmpeg)
│   ├── logger.py         # Logging configuration
│   ├── ai/               # AI-powered features (LLM integration)
│   ├── animation/        # Animation system
│   ├── api/              # External API integrations
│   ├── cli/              # Command-line interface (Typer)
│   ├── common/           # Shared types and utilities
│   ├── effect/           # Text, clip, and sound effects
│   ├── layout/           # Subtitle layout calculation
│   ├── pipeline/         # Core processing pipeline
│   ├── renderer/         # Subtitle rendering engines
│   ├── selector/         # Word/clip selection logic
│   ├── tag/              # Tagging system
│   ├── template/         # Template management
│   ├── transcriber/      # Audio transcription
│   ├── utils/            # Utility functions
│   └── video/            # Video generation
├── docs/                 # Documentation
└── pyproject.toml        # Project configuration
```

## Core Modules

### 1. Pipeline (`pipeline/`)

The heart of pycaps. Orchestrates the entire video processing workflow.

- **`CapsPipelineBuilder`**: Fluent API for configuring the pipeline
- **`CapsPipeline`**: Executes the processing stages
- **`JsonConfigLoader`**: Loads configuration from JSON files
- **`SubtitleDataService`**: Manages subtitle data persistence

```python
pipeline = (
    CapsPipelineBuilder()
    .with_input_video("input.mp4")
    .add_css("styles.css")
    .build()
)
pipeline.run()
```

### 2. Transcriber (`transcriber/`)

Handles audio-to-text conversion with word-level timestamps.

- **`WhisperAudioTranscriber`**: OpenAI Whisper-based transcription
- **`GoogleAudioTranscriber`**: Google Cloud Speech-to-Text
- **`PreviewTranscriber`**: Dummy transcriber for previews
- **Splitters**: Segment splitting strategies
  - `LimitByWordsSplitter`: Split by word count
  - `LimitByCharsSplitter`: Split by character count
  - `SplitIntoSentencesSplitter`: Split by sentences
- **`TranscriptionEditor`**: GUI for editing transcriptions

### 3. Renderer (`renderer/`)

Generates subtitle images from styled text.

- **`CssSubtitleRenderer`**: Playwright-based CSS rendering (full CSS support)
- **`PictexSubtitleRenderer`**: Lightweight rendering without browser (limited CSS)
- **`PlaywrightScreenshotCapturer`**: Browser screenshot utility
- **`RendererPage`**: HTML page generation for rendering
- **Caching**: `LetterSizeCache`, `RenderedImageCache`

### 4. Animation (`animation/`)

Provides dynamic visual effects for subtitles.

- Built-in animations: FadeIn, FadeOut, Pop, Slide, etc.
- **`ElementAnimator`**: Applies animations to elements
- Triggered by events: `ON_NARRATION_STARTS`, `ON_NARRATION_ENDS`, etc.

### 5. Effect (`effect/`)

Three types of effects:

- **`TextEffect`**: Modifies text content (e.g., typewriting effect)
- **`ClipEffect`**: Modifies video clips
- **`SoundEffect`**: Adds audio effects

### 6. Layout (`layout/`)

Calculates subtitle positioning and line breaking.

- **`SubtitleLayoutOptions`**: Layout configuration
- **`LineSplitter`**: Breaks text into lines
- **`PositionsCalculator`**: Computes element positions
- **`WordSizeCalculator`**: Measures word dimensions
- **`LayoutUpdater`**: Updates layout based on viewport

### 7. Template (`template/`)

Manages reusable style configurations.

- **`TemplateLoader`**: Loads templates by name
- **`TemplateFactory`**: Creates template instances
- **`BuiltinTemplate`**: Pre-packaged templates
- **`LocalTemplate`**: User-created templates

### 8. Tag (`tag/`)

Enables conditional styling based on word properties.

- **`SemanticTagger`**: Tags based on meaning (e.g., highlight keywords)
- **`StructureTagger`**: Tags based on position (e.g., first-word-in-line)
- **`TagCondition`**: Filters elements by tags
- **`BuiltinTag`**: Predefined tag types

### 9. Selector (`selector/`)

Selects elements for animations/effects.

- **`WordClipSelector`**: Selects word clips
- **`TimeEventSelector`**: Selects by time
- **`TagBasedSelector`**: Selects by tags

### 10. Video (`video/`)

Handles final video composition.

- **`VideoGenerator`**: Combines video, audio, and subtitles
- **`SubtitleClipsGenerator`**: Creates subtitle clip sequences
- **`AudioUtils`**: Audio processing utilities

### 11. CLI (`cli/`)

Command-line interface built with Typer.

- `pycaps render`: Render video with subtitles
- `pycaps preview-styles`: Live CSS preview
- `pycaps template`: Template management
- `pycaps config`: API key configuration

### 12. AI (`ai/`)

AI-powered features.

- **`LlmProvider`**: Language model integration for intelligent tagging

## Data Model

The subtitle data follows a hierarchical structure:

```
Document
└── Segment (sentence/phrase)
    └── Line (visual line)
        └── Word (single word with timing)
            └── WordClip (visual state instance)
```

### WordClip States

Each word generates multiple clips for different narration states:
1. **Not Narrated Yet**: Before the word is spoken
2. **Being Narrated**: During pronunciation
3. **Already Narrated**: After pronunciation

This enables CSS targeting like `.word-being-narrated` for dynamic styling.

## Processing Pipeline Flow

```
1. Input Video
      ↓
2. Audio Extraction
      ↓
3. Transcription (Whisper/Google)
      ↓
4. Segment Splitting
      ↓
5. Tagging (Semantic + Structure)
      ↓
6. Layout Calculation
      ↓
7. Animation/Effect Application
      ↓
8. Subtitle Rendering (CSS → Images)
      ↓
9. Video Composition
      ↓
10. Output Video
```

## Key Dependencies

- **Whisper**: OpenAI's speech recognition model
- **Playwright**: Browser automation for CSS rendering
- **MoviePy (movielite)**: Video editing
- **Typer**: CLI framework
- **Pydantic**: Data validation
- **Pillow**: Image processing
- **FFmpeg**: Audio/video processing (external)

## Configuration

pycaps supports two configuration methods:

1. **Template-based**: Use predefined or custom templates
2. **JSON-based**: Full configuration via JSON files (see `CONFIG_REFERENCE.md`)

## Rendering Engines

| Renderer | Pros | Cons |
|----------|------|------|
| `CssSubtitleRenderer` | Full CSS support, accurate rendering | Requires Playwright/Chromium |
| `PictexSubtitleRenderer` | Lightweight, no browser | Limited CSS support, some visual differences |

## Getting Started for Development

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (Unix) or `venv\Scripts\activate` (Windows)
4. Install with dev dependencies: `pip install -e ".[all]"`
5. Install Playwright browsers: `playwright install chromium`
6. Ensure FFmpeg is installed and in PATH

## See Also

- [CLI Usage Guide](./CLI.md)
- [Core Structure](./CORE_STRUCTURE.md)
- [Tagging System](./TAGS.md)
- [Templates](./TEMPLATES.md)
- [Configuration Reference](./CONFIG_REFERENCE.md)
- [Examples](./EXAMPLES.md)
- [API Usage](./API_USAGE.md)
