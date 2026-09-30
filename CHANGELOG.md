# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added faster-whisper as an alternative transcription backend - Faster and lighter than openai-whisper, especially on CPU. It can be selected with `--whisper-backend faster`, `"backend": "faster"` in the `whisper` config, or `with_whisper_config(backend=WhisperBackend.FASTER)`, and it's available as the `faster-whisper` extra ([#20](https://github.com/francozanardi/pycaps/issues/20)).
- Added external transcript input - Captions can be generated from an existing transcript (Whisper JSON, pycaps JSON, SRT or VTT) instead of transcribing the audio, via `with_transcription()` / `with_transcription_file()` or the `--transcript` and `--transcript-format` CLI flags ([#11](https://github.com/francozanardi/pycaps/issues/11)).

### Removed

- Removed the Pycaps API, which was deprecated and is no longer available - The `pycaps config` command (used to set its API key) was removed, and the AI features (`ai` tagger rules and `emoji_in_segment`) now use only your own OpenAI API key, set with the `PYCAPS_OPENAI_API_KEY` environment variable. See [AI Features](docs/API_USAGE.md).

### Fixed

- Fixed custom sound effects from JSON configs - They always failed because `when` and `what` were swapped, and their `path` is now relative to the config file, like the other paths.
- Fixed `ModifyWordsEffect` without a `tag_condition` - It didn't modify any word, instead of modifying all of them.
- Fixed `pycaps render --config` ignoring `--input` - Configs without an `input` field failed with "Input video path is required".
- Fixed CSS being lost when replacing the subtitle renderer - Calling `with_custom_subtitle_renderer()` after adding CSS (e.g. after loading a template) dropped the styles, so words rendered without the template styles and with no gaps between them ([#21](https://github.com/francozanardi/pycaps/issues/21), [#22](https://github.com/francozanardi/pycaps/issues/22)).

## [0.2.1] - 2026-01-10

### Fixed

- Fixed subtitle scaling issue - Subtitles were not scaling correctly when the video resolution was changed.

## [0.2.0] - 2025-11-15

### Changed

- Migrated from custom rendering logic to movielite library
