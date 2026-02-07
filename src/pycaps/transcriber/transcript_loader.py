from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from pycaps.common import Document, Line, Segment, TimeFragment, Word

from .transcript_format import TranscriptFormat

_TIME_EPSILON = 0.01
_VTT_INLINE_TIME_RE = re.compile(r"<((?:\d{2}:)?\d{2}:\d{2}\.\d{3})>")


def load_transcription(source: Document | dict[str, Any] | str, format: TranscriptFormat | str = TranscriptFormat.AUTO) -> Document:
    resolved_format = _resolve_format(format)

    if isinstance(source, Document):
        return _normalize_document(source)

    if isinstance(source, dict):
        return _load_from_dict(source, resolved_format)

    if isinstance(source, str):
        source_path = Path(source)
        if not source_path.exists():
            raise ValueError(f"Transcription file not found: {source}")
        if not source_path.is_file():
            raise ValueError(f"Transcription path is not a file: {source}")
        return _load_from_path(source_path, resolved_format)

    raise ValueError("Invalid transcription source. Expected Document, dict, or file path.")


def _load_from_path(path: Path, requested_format: TranscriptFormat) -> Document:
    suffix = path.suffix.lower()
    content = path.read_text(encoding="utf-8")
    resolved_format = requested_format

    if requested_format == TranscriptFormat.AUTO:
        if suffix == ".srt":
            resolved_format = TranscriptFormat.SRT
        elif suffix == ".vtt":
            resolved_format = TranscriptFormat.VTT
        else:
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Could not parse transcription file as JSON: {path}") from e
            return _load_from_dict(data, TranscriptFormat.AUTO)

    if resolved_format == TranscriptFormat.SRT:
        return _parse_srt(content)
    if resolved_format == TranscriptFormat.VTT:
        return _parse_vtt(content)

    if resolved_format in (TranscriptFormat.WHISPER_JSON, TranscriptFormat.PYCAPS_JSON):
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse transcription file as JSON: {path}") from e
        return _load_from_dict(data, resolved_format)

    raise ValueError(f"Unsupported transcript format: {resolved_format.value}")


def _load_from_dict(data: dict[str, Any], requested_format: TranscriptFormat) -> Document:
    resolved_format = requested_format if requested_format != TranscriptFormat.AUTO else _detect_json_format(data)
    if resolved_format == TranscriptFormat.WHISPER_JSON:
        document = _parse_whisper_json(data)
    elif resolved_format == TranscriptFormat.PYCAPS_JSON:
        document = _parse_pycaps_json(data)
    else:
        raise ValueError(f"Format '{resolved_format.value}' requires a text subtitle file path.")
    return _normalize_document(document)


def _detect_json_format(data: dict[str, Any]) -> TranscriptFormat:
    segments = data.get("segments")
    if not isinstance(segments, list):
        raise ValueError("Invalid transcript JSON: expected a top-level 'segments' array.")

    first_segment = next((segment for segment in segments if isinstance(segment, dict)), None)
    if first_segment is None:
        return TranscriptFormat.PYCAPS_JSON

    if isinstance(first_segment.get("lines"), list):
        return TranscriptFormat.PYCAPS_JSON

    words = first_segment.get("words")
    if isinstance(words, list):
        if "language" in data or "text" in first_segment or "id" in first_segment:
            return TranscriptFormat.WHISPER_JSON
        first_word = next((word for word in words if isinstance(word, dict)), None)
        if first_word and "word" in first_word and "time" not in first_word:
            return TranscriptFormat.WHISPER_JSON
        return TranscriptFormat.PYCAPS_JSON

    return TranscriptFormat.PYCAPS_JSON


def _parse_whisper_json(data: dict[str, Any]) -> Document:
    segments_data = data.get("segments")
    if not isinstance(segments_data, list):
        raise ValueError("Invalid whisper_json: expected 'segments' array.")

    document = Document()
    for segment_data in segments_data:
        if not isinstance(segment_data, dict):
            continue
        words = _parse_words_from_entries(segment_data.get("words"))
        if not words:
            segment_text = str(segment_data.get("text", "")).strip()
            segment_start = _to_float(segment_data.get("start"))
            segment_end = _to_float(segment_data.get("end"))
            if segment_text and segment_start is not None and segment_end is not None:
                words = _build_words_with_proportional_timing(segment_text, segment_start, segment_end)
        _append_segment_from_words(document, words)
    return document


def _parse_pycaps_json(data: dict[str, Any]) -> Document:
    segments_data = data.get("segments")
    if not isinstance(segments_data, list):
        raise ValueError("Invalid pycaps_json: expected 'segments' array.")

    document = Document()
    for segment_data in segments_data:
        if not isinstance(segment_data, dict):
            continue

        words: list[Word] = []
        if isinstance(segment_data.get("lines"), list):
            for line_data in segment_data["lines"]:
                if not isinstance(line_data, dict):
                    continue
                words.extend(_parse_words_from_entries(line_data.get("words")))
        elif isinstance(segment_data.get("words"), list):
            words.extend(_parse_words_from_entries(segment_data.get("words")))
        elif "text" in segment_data:
            segment_text = str(segment_data.get("text", "")).strip()
            segment_start, segment_end = _extract_entry_time(segment_data)
            if segment_text and segment_start is not None and segment_end is not None:
                words.extend(_build_words_with_proportional_timing(segment_text, segment_start, segment_end))

        _append_segment_from_words(document, words)
    return document


def _parse_srt(content: str) -> Document:
    document = Document()
    for cue in _parse_subtitle_cues(content, format=TranscriptFormat.SRT):
        words = _build_words_with_proportional_timing(cue["text"], cue["start"], cue["end"])
        _append_segment_from_words(document, words)
    return document


def _parse_vtt(content: str) -> Document:
    document = Document()
    for cue in _parse_subtitle_cues(content, format=TranscriptFormat.VTT):
        words = _parse_vtt_inline_words(cue["text"], cue["start"], cue["end"])
        if not words:
            cleaned_text = _clean_caption_text(cue["text"])
            words = _build_words_with_proportional_timing(cleaned_text, cue["start"], cue["end"])
        _append_segment_from_words(document, words)
    return document


def _parse_subtitle_cues(content: str, format: TranscriptFormat) -> list[dict[str, Any]]:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", normalized.strip())
    cues: list[dict[str, Any]] = []

    for block in blocks:
        lines = [line.rstrip() for line in block.split("\n") if line.strip() != ""]
        if not lines:
            continue

        first_line = lines[0].strip()
        if format == TranscriptFormat.VTT:
            if first_line.startswith("\ufeff"):
                first_line = first_line.removeprefix("\ufeff")
            if first_line.startswith("WEBVTT"):
                continue
            if first_line.startswith(("NOTE", "STYLE", "REGION")):
                continue

        timing_index = 0 if "-->" in lines[0] else 1 if len(lines) > 1 and "-->" in lines[1] else -1
        if timing_index == -1:
            continue

        start, end = _parse_timing_line(lines[timing_index])
        text_lines = lines[timing_index + 1 :]
        text = "\n".join(text_lines).strip()
        if not text:
            continue

        cues.append({"start": start, "end": end, "text": text})

    return cues


def _parse_timing_line(line: str) -> tuple[float, float]:
    parts = line.split("-->")
    if len(parts) != 2:
        raise ValueError(f"Invalid subtitle timing line: {line}")

    start_raw = parts[0].strip().split(" ")[0]
    end_raw = parts[1].strip().split(" ")[0]
    start = _parse_timestamp(start_raw)
    end = _parse_timestamp(end_raw)
    return _sanitize_time_range(start, end)


def _parse_vtt_inline_words(cue_text: str, cue_start: float, cue_end: float) -> list[Word]:
    content = cue_text.replace("\n", " ")
    matches = list(_VTT_INLINE_TIME_RE.finditer(content))
    if not matches:
        return []

    words: list[Word] = []
    prefix_text = _clean_caption_text(content[: matches[0].start()])
    first_anchor = min(cue_end, _parse_timestamp(matches[0].group(1)))
    words.extend(_build_words_with_proportional_timing(prefix_text, cue_start, first_anchor))

    for index, match in enumerate(matches):
        interval_start = max(cue_start, _parse_timestamp(match.group(1)))
        interval_end = cue_end
        if index + 1 < len(matches):
            interval_end = min(cue_end, _parse_timestamp(matches[index + 1].group(1)))

        chunk_start = match.end()
        chunk_end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        chunk_text = _clean_caption_text(content[chunk_start:chunk_end])
        words.extend(_build_words_with_proportional_timing(chunk_text, interval_start, interval_end))

    return words


def _build_words_with_proportional_timing(text: str, start: float, end: float) -> list[Word]:
    words_text = _split_words(text)
    if not words_text:
        return []

    start, end = _sanitize_time_range(start, end)
    if len(words_text) == 1:
        return [Word(text=words_text[0], time=TimeFragment(start=start, end=end))]

    weights = [max(len(word), 1) for word in words_text]
    total_weight = sum(weights)
    duration = end - start

    words: list[Word] = []
    consumed_weight = 0
    for index, (word_text, weight) in enumerate(zip(words_text, weights)):
        word_start = start + duration * (consumed_weight / total_weight)
        consumed_weight += weight
        word_end = end if index == len(words_text) - 1 else start + duration * (consumed_weight / total_weight)
        word_start, word_end = _sanitize_time_range(word_start, word_end)
        words.append(Word(text=word_text, time=TimeFragment(start=word_start, end=word_end)))

    return words


def _parse_words_from_entries(entries: Any) -> list[Word]:
    if not isinstance(entries, list):
        return []

    words: list[Word] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        text = str(entry.get("text", entry.get("word", ""))).strip()
        if not text:
            continue

        start, end = _extract_entry_time(entry)
        if start is None or end is None:
            continue
        start, end = _sanitize_time_range(start, end)
        words.append(Word(text=text, time=TimeFragment(start=start, end=end)))

    return words


def _extract_entry_time(entry: dict[str, Any]) -> tuple[float | None, float | None]:
    if isinstance(entry.get("time"), dict):
        time_data = entry["time"]
        return _to_float(time_data.get("start")), _to_float(time_data.get("end"))
    return _to_float(entry.get("start")), _to_float(entry.get("end"))


def _append_segment_from_words(document: Document, words: list[Word]) -> None:
    cleaned_words = [word for word in words if word.text.strip()]
    if not cleaned_words:
        return

    segment_start = cleaned_words[0].time.start
    segment_end = cleaned_words[-1].time.end
    segment_start, segment_end = _sanitize_time_range(segment_start, segment_end)
    segment_time = TimeFragment(start=segment_start, end=segment_end)

    segment = Segment(time=segment_time)
    line = Line(time=segment_time)
    line.words.set_all(cleaned_words)
    segment.lines.add(line)
    document.segments.add(segment)


def _normalize_document(document: Document) -> Document:
    normalized_document = Document()
    for segment in document.segments:
        words: list[Word] = []
        for line in segment.lines:
            for word in line.words:
                text = str(word.text).strip()
                if not text:
                    continue
                start, end = _sanitize_time_range(word.time.start, word.time.end)
                words.append(Word(text=text, time=TimeFragment(start=start, end=end)))
        _append_segment_from_words(normalized_document, words)
    return normalized_document


def _split_words(text: str) -> list[str]:
    return [token for token in re.split(r"\s+", text.strip()) if token]


def _clean_caption_text(text: str) -> str:
    return html.unescape(re.sub(r"</?[^>]+>", "", text)).strip()


def _parse_timestamp(value: str) -> float:
    cleaned = value.strip().replace(",", ".")
    if not cleaned:
        raise ValueError("Invalid empty timestamp.")

    parts = cleaned.split(":")
    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
    elif len(parts) == 2:
        hours = 0
        minutes = int(parts[0])
        seconds = float(parts[1])
    else:
        raise ValueError(f"Invalid timestamp format: {value}")

    return hours * 3600 + minutes * 60 + seconds


def _sanitize_time_range(start: float, end: float) -> tuple[float, float]:
    start = max(0.0, float(start))
    end = max(0.0, float(end))
    if end <= start:
        end = start + _TIME_EPSILON
    return start, end


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _resolve_format(format: TranscriptFormat | str) -> TranscriptFormat:
    if isinstance(format, TranscriptFormat):
        return format
    if isinstance(format, str):
        normalized = format.strip().lower()
        try:
            return TranscriptFormat(normalized)
        except ValueError as e:
            raise ValueError(
                "Invalid transcript format. Expected one of: auto, whisper_json, pycaps_json, srt, vtt."
            ) from e
    raise ValueError("Invalid transcript format type. Expected TranscriptFormat or str.")
