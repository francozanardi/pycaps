# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added external transcript input - Captions can be generated from an existing transcript (Whisper JSON, pycaps JSON, SRT or VTT) instead of transcribing the audio, via `with_transcription()` / `with_transcription_file()` or the `--transcript` and `--transcript-format` CLI flags ([#11](https://github.com/francozanardi/pycaps/issues/11)).

### Fixed

- Fixed CSS being lost when replacing the subtitle renderer - Calling `with_custom_subtitle_renderer()` after adding CSS (e.g. after loading a template) dropped the styles, so words rendered without the template styles and with no gaps between them ([#21](https://github.com/francozanardi/pycaps/issues/21), [#22](https://github.com/francozanardi/pycaps/issues/22)).

## [0.2.1] - 2026-01-10

### Fixed

- Fixed subtitle scaling issue - Subtitles were not scaling correctly when the video resolution was changed.

## [0.2.0] - 2025-11-15

### Changed

- Migrated from custom rendering logic to movielite library
