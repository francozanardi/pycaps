# Templates Guide

Templates are the most convenient way to create reusable and shareable styles in `pycaps`. A template is a self-contained directory that bundles together configuration, styles, and resources.

## What is a Template?

A `pycaps` template is simply a folder that contains:
1.  A `pycaps.template.json` configuration file.
2.  A CSS stylesheet (usually `styles.css`).
3.  An optional `resources` folder for assets like fonts or images.

### Template Directory Structure

A typical template looks like this:

```
my-awesome-template/
├── pycaps.template.json  # Main configuration for the pipeline
├── styles.css            # All CSS styles for the subtitles
└── resources/            # Optional folder for assets
    └── my-font.ttf
```

The paths inside `pycaps.template.json` (like for `css` and `resources`) should be relative to the file itself.

## Using a Template

You can use a template from both the CLI and Python.

### From the CLI

Use the `--template` option. `pycaps` will look for a template with that name first in your current working directory (a local template) and then in its built-in templates.

```bash
pycaps render --input my_video.mp4 --template my-awesome-template
```

### From Python

Use the `TemplateLoader` to initialize a pipeline builder directly from a template.

```python
from pycaps import TemplateLoader, VideoQuality

# Load a builder from a template named 'my-awesome-template'
builder = TemplateLoader("my-awesome-template").with_input_video("my_video.mp4").load(False)

# You can further customize the builder here if needed
builder.with_video_quality(VideoQuality.HIGH)

# Build and run
pipeline = builder.build()
pipeline.run()
```

## Creating a New Template

The easiest way to create a new template is with the CLI.

### Step 1: Create the Template Directory

Run the `template create` command. This will copy an existing template (by default, the `default` built-in one) to a new folder.

```bash
# Creates a new folder named 'my-new-style' in the current directory
pycaps template create --name my-new-style
```
This gives you a solid starting point with a working `pycaps.template.json` and `styles.css`. You can also start from any other template with `--from`, for example `pycaps template create --name my-new-style --from hype`.

### Step 2: Customize Your Template

Now, you can edit the files inside the `my-new-style` directory:

1.  **Edit `styles.css`**: Change the fonts, colors, sizes, and backgrounds to match your brand.
2.  **Add resources**: Place any custom fonts or images into the `resources/` folder and reference them in your CSS.
3.  **Edit `pycaps.template.json`**: Modify the animations, effects, layout, and other pipeline settings. The [Effects & Animations Guide](./EFFECTS_AND_ANIMATIONS.md) explains them step by step, and the [Configuration Reference](./CONFIG_REFERENCE.md) lists all the options.

Once customized, your template is ready to be used with the `--template my-new-style` flag.
