import typer
from .template_cli import template_app
from .render_cli import render_app
from .preview_styles_cli import preview_app

app = typer.Typer(
    help="Pycaps, a tool for adding CSS-styled subtitles to videos",
    invoke_without_command=True,
    add_completion=False,
)
app.add_typer(render_app)
app.add_typer(preview_app)
app.add_typer(template_app, name="template")

@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


