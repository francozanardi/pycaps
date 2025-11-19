import typer
from typing import Optional
from pycaps.logger import set_logging_level
import logging
from pycaps.pipeline import JsonConfigLoader
from pycaps.common import VideoQuality
from pycaps.layout import VerticalAlignmentType, SubtitleLayoutOptions
from pycaps.template import TemplateLoader, DEFAULT_TEMPLATE_NAME, TemplateFactory
from pycaps.transcriber import ElevenLabsAlignmentTranscriber

render_app = typer.Typer()

def _parse_styles(styles: list[str]) -> str:
    parsed_styles = {}
    for style in styles:
        selector, value = style.split(".")
        if not selector.startswith("."):
            selector = f".{selector}".strip()
        property, value = value.split("=")
        if selector not in parsed_styles:
            parsed_styles[selector] = "\n"
        parsed_styles[selector] += f"{property.strip()}: {value.strip()};\n"

    return "\n".join([f"{selector} {{ {styles} }}" for selector, styles in parsed_styles.items()])

def _parse_preview(preview: bool, preview_time: Optional[str]) -> Optional[tuple[float, float]]:
    if not preview and not preview_time:
        return None
    final_preview = tuple(map(float, preview_time.split(","))) if preview_time else (0, 5)
    if len(final_preview) != 2 or final_preview[0] < 0 or final_preview[1] < 0 or final_preview[0] >= final_preview[1]:
        typer.echo(f"Invalid preview time: {final_preview}, example: --preview-time=10,15", err=True)
        return None
    return final_preview

def _build_layout_options(builder, align, offset) -> SubtitleLayoutOptions:
    original_layout = builder._caps_pipeline._layout_options # TODO: fix this
    original_vertical_align = original_layout.vertical_align
    new_vertical_align = original_vertical_align.model_copy(update={
        "align": align or original_vertical_align.align,
        "offset": offset or 0
    })
    return original_layout.model_copy(update={"vertical_align": new_vertical_align})

@render_app.command("render", help="Render a video with subtitles using templates or custom configs. Supports Whisper transcription, styles override, layouts, and preview modes.")
def render(
    input: str = typer.Option(..., "--input", help="Input video file name", rich_help_panel="Main options", show_default=False),
    output: Optional[str] = typer.Option(None, "--output", help="Output video file name", rich_help_panel="Main options", show_default=False),
    template_name: Optional[str] = typer.Option(None, "--template", help="Template name. If no template and no config file is provided, the default template will be used", rich_help_panel="Main options", show_default=False),
    config_file: Optional[str] = typer.Option(None, "--config", help="Config JSON file path", rich_help_panel="Main options", show_default=False),
    transcription_preview: bool = typer.Option(False, "--transcription-preview", help="Stops the rendering process and shows an editable preview of the transcription", rich_help_panel="Main options", show_default=False),

    layout_align: Optional[VerticalAlignmentType] = typer.Option(None, "--layout-align", help="Vertical alignment for subtitles", rich_help_panel="Layout", show_default=False),
    layout_align_offset: Optional[float] = typer.Option(None, "--layout-align-offset", help="Vertical alignment offset. Positive values move the subtitles down, negative values move them up", rich_help_panel="Layout", show_default=False),

    style: list[str] = typer.Option(None, "--style", help="Override styles of the template, example: --style word.color=red", rich_help_panel="Style", show_default=False),

    language: Optional[str] = typer.Option(None, "--lang", help="Language of the video, example: --lang=en", rich_help_panel="Whisper", show_default=False),
    whisper_model: Optional[str] = typer.Option(None, "--whisper-model", help="Whisper model to use, example: --whisper-model=base", rich_help_panel="Whisper", show_default=False),

    video_quality: Optional[VideoQuality] = typer.Option(None, "--video-quality", help="Final video quality", rich_help_panel="Video", show_default=False),

    preview: bool = typer.Option(False, "--preview", help="Generate a low quality preview of the rendered video", rich_help_panel="Utils"),
    preview_time: Optional[str] = typer.Option(None, "--preview-time", help="Generate a low quality preview of the rendered video at the given time, example: --preview-time=10,15", rich_help_panel="Utils", show_default=False),
    subtitle_data: Optional[str] = typer.Option(None, "--subtitle-data", help="Subtitle data file path. If provided, the rendering process will skip the transcription and tagging steps", rich_help_panel="Utils", show_default=False),
    elevenlabs_alignment: Optional[str] = typer.Option(None, "--elevenlabs-alignment", help="Eleven Labs alignment JSON file path. Use this to skip Whisper transcription and use pre-generated alignment data from Eleven Labs TTS API", rich_help_panel="Utils", show_default=False),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose mode", rich_help_panel="Utils"),
):
    set_logging_level(logging.DEBUG if verbose else logging.INFO)
    if template_name and config_file:
        typer.echo("Only one of --template or --config can be provided", err=True)
        return None
    
    if not template_name and not config_file:
        template_name = DEFAULT_TEMPLATE_NAME
    
    if template_name:
        typer.echo(f"Rendering {input} with template {template_name}...")
        template = TemplateFactory().create(template_name)
        builder = TemplateLoader(template).with_input_video(input).load(False)
    elif config_file:
        typer.echo(f"Rendering {input} with config file {config_file}...")
        builder = JsonConfigLoader(config_file).load(False)
        
    if output: builder.with_output_video(output)
    if style: builder.add_css_content(_parse_styles(style))
    # TODO: this has a little issue (if you set lang via js + whisper model by cli, it will change the lang to None)
    if language or whisper_model: builder.with_whisper_config(language=language, model_size=whisper_model if whisper_model else "base")
    if subtitle_data: builder.with_subtitle_data_path(subtitle_data)
    if elevenlabs_alignment: builder.with_custom_audio_transcriber(ElevenLabsAlignmentTranscriber(elevenlabs_alignment))
    if transcription_preview: builder.should_preview_transcription(True)
    if video_quality: builder.with_video_quality(video_quality)
    if layout_align or layout_align_offset: builder.with_layout_options(_build_layout_options(builder, layout_align, layout_align_offset))

    pipeline = builder.build(preview_time=_parse_preview(preview, preview_time))
    pipeline.run()
