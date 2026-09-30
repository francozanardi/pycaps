# AI Features

Some features of pycaps use a Large Language Model (LLM) to understand the context of your script:

- The `ai` rules of the semantic tagger, which tag words based on a description (see the [Tagging System](./TAGS.md)).
- The `emoji_in_segment` effect, which adds relevant emojis to the subtitles (see the [Effects & Animations Guide](./EFFECTS_AND_ANIMATIONS.md#emoji_in_segment)).

These features use the OpenAI API, so they need your own OpenAI API key. Everything else in pycaps runs locally, without an API key.

## How to set up

1.  Install the OpenAI client:

    ```bash
    pip install openai
    ```

2.  Set an environment variable named `PYCAPS_OPENAI_API_KEY` with your OpenAI API key.

    **On macOS/Linux:**
    ```bash
    export PYCAPS_OPENAI_API_KEY="sk-YourOpenAIKeyHere"
    ```
    You can add this line to your shell profile (e.g., `~/.zshrc`, `~/.bash_profile`) to make it permanent.

    **On Windows (Command Prompt):**
    ```powershell
    setx PYCAPS_OPENAI_API_KEY "sk-YourOpenAIKeyHere"
    ```
    You may need to restart your terminal for the change to take effect.

If the environment variable is not set, the AI features are skipped and a warning is logged, but the video is still rendered.
