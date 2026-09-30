from typing import Dict
from pycaps.common import Tag
from .external_llm_tagger import ExternalLlmTagger
from pycaps.ai import LlmProvider
from pycaps.logger import logger

class AiTagger:
    def process(self, text: str, rules: Dict[Tag, str]) -> str:
        """
        Process text using AI to identify and tag relevant terms according to given rules.

        Args:
            text: The text to analyze
            rules: Dictionary mapping tags to their topics (e.g., {Tag('emotion'): 'emotions and feelings'})

        Returns:
            Text with XML-like tags around relevant terms
            Example: "I feel <emotion>happy</emotion> about my <finance>investment</finance>"
        """
        if not LlmProvider.get().is_enabled():
            logger().warning("The LLM provider is not enabled. Ignoring AI tagging rules.")
            return text

        return ExternalLlmTagger().process(text, rules)
