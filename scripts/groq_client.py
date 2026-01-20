"""GROQ API client for AI draft generation."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from groq import Groq

logger = logging.getLogger(__name__)


class GroqClient:
    """Client for interacting with GROQ API."""

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """Initialize GROQ client."""
        if not api_key or not api_key.strip():
            raise ValueError("GROQ API key cannot be empty")

        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _call_api(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        temperature: float | None = None,
        use_json_mode: bool = False,
    ) -> str:
        """Make API call to GROQ with retry logic."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }
        if use_json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        # Retry logic with exponential backoff
        max_retries = 5
        for attempt in range(max_retries):
            try:
                logger.info(f"GROQ API call attempt {attempt + 1}/{max_retries}")
                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content or ""
                logger.info(
                    f"GROQ API call successful (response length: {len(content)} chars)"
                )
                return content
            except Exception as e:
                logger.warning(
                    f"GROQ API error on attempt {attempt + 1}/{max_retries}: {type(e).__name__}: {e}"
                )

                # Don't retry on auth errors or bad requests
                error_str = str(e).lower()
                if any(
                    x in error_str
                    for x in ["auth", "api key", "unauthorized", "forbidden"]
                ):
                    logger.error("Authentication error - not retrying")
                    raise

                if attempt < max_retries - 1:
                    # Exponential backoff: 2, 4, 8, 16 seconds
                    sleep_time = 2 ** (attempt + 1)
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"All {max_retries} attempts failed")
                    raise RuntimeError(
                        f"GROQ API not reachable after {max_retries} retries: {e}"
                    ) from e

    def generate_search_queries(
        self, title: str, category: str, url: str = ""
    ) -> dict[str, Any]:
        """
        Pass 1: Generate 3-5 search queries for a topic.

        Returns:
            {
                "queries": ["query1", "query2", ...],
                "reasoning": "why these queries"
            }
        """
        category_hints = {
            "research": "Focus on methodology, results, related work, and criticisms. Target academic and technical sources.",
            "technologies": "Focus on use cases, tutorials, comparisons with alternatives, best practices, and trade-offs.",
            "general": "Focus on clear explanations, examples, common misconceptions, and practical applications.",
            "math": "Focus on theorem statements, proofs, intuitive explanations, worked examples, and visualizations.",
            "books": "Focus on summaries, key takeaways, critical analysis, chapter summaries, and author background.",
        }

        hint = category_hints.get(category, category_hints["general"])

        url_context = f"\n\nSource URL: {url}" if url else ""

        prompt = f"""Generate 3-5 search queries to research the following topic for documentation purposes.

Topic: {title}
Category: {category}
{hint}{url_context}

Generate queries that will help create comprehensive documentation covering:
- Core concepts and definitions
- Methodology or how it works
- Examples and applications
- Comparisons and alternatives (if applicable)
- Critical analysis and limitations

Return ONLY a JSON object with this structure:
{{
  "queries": ["query1", "query2", "query3", "query4", "query5"],
  "reasoning": "brief explanation of query strategy"
}}

Make queries specific and targeted to find high-quality sources."""

        messages = [
            {
                "role": "system",
                "content": "You are a research assistant helping generate targeted search queries. Always respond with valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ]

        response = self._call_api(messages, max_tokens=1000, use_json_mode=True)

        try:
            result = json.loads(response)
            # Validate structure
            if "queries" not in result or not isinstance(result["queries"], list):
                raise ValueError("Invalid response structure")

            # Validate not empty
            if len(result["queries"]) < 1:
                raise ValueError("No queries generated")

            # Limit to 5 queries
            result["queries"] = result["queries"][:5]

            return result
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse GROQ response: {e}")
            # Fallback: simple queries from title
            return {
                "queries": [
                    f"{title} overview",
                    f"{title} explained",
                    f"{title} examples",
                ],
                "reasoning": "Fallback queries due to parsing error",
            }

    def synthesize_outline(
        self, title: str, category: str, sources: str, template: str, url: str = ""
    ) -> str:
        """
        Pass 3: Synthesize sources into structured outline.

        Args:
            title: Topic title
            category: Category (research/tech/etc)
            sources: Formatted string of all search results
            template: Target template structure
            url: Original URL if provided

        Returns:
            Markdown outline
        """
        url_context = f"\n\nOriginal Source: {url}" if url else ""

        prompt = f"""Create a structured outline for documentation on this topic using the provided sources.

Topic: {title}
Category: {category}{url_context}

=== SOURCES ===
{sources}

=== TARGET TEMPLATE ===
{template}

Your task:
1. Read and understand all sources
2. Identify key themes and concepts
3. Map themes to template sections
4. Create bullet-point outline for each section
5. Note which sections have strong vs weak source coverage
6. Adapt template structure to content type:
   - Research: emphasize methodology, results, related work
   - Technologies: highlight use cases, trade-offs, comparisons
   - Concepts: focus on explanation, examples, applications
   - Math: prioritize intuition, proofs, examples
   - Books: extract key takeaways, themes, quotes

Return a markdown outline with:
- Section headers matching template
- Bullet points under each section
- Comments like [Strong sources: N] or [Weak sources, TODO] for each section

Be flexible with template - adapt structure to fit the content naturally."""

        messages = [
            {
                "role": "system",
                "content": "You are a research synthesizer creating structured outlines from sources. Be clear, organized, and adapt structure to content.",
            },
            {"role": "user", "content": prompt},
        ]

        return self._call_api(messages, max_tokens=3000)

    def expand_to_draft(
        self, title: str, category: str, outline: str, sources: str
    ) -> str:
        """
        Pass 4: Expand outline into full draft document.

        Args:
            title: Topic title
            category: Category
            outline: Structured outline from Pass 3
            sources: All source content

        Returns:
            Complete markdown document
        """
        prompt = f"""Expand this outline into a complete, well-written documentation article.

Topic: {title}
Category: {category}

=== OUTLINE ===
{outline}

=== SOURCES (for reference) ===
{sources}

Your task:
1. Expand each bullet point into clear prose
2. Maintain outline structure but adapt as needed
3. Write in educational, clear style
4. Include examples from sources where available
5. Add TODO comments for sections with weak source coverage
6. Target 800-1500 words total
7. Include proper markdown formatting
8. Add all source URLs to References section

Guidelines:
- Write for future self who wants to understand this topic
- Explain concepts simply before diving deep
- Use analogies and examples
- Don't just copy sources - synthesize and explain
- Leave TODOs for manual additions (personal insights, etc)

Return complete markdown document ready for review."""

        messages = [
            {
                "role": "system",
                "content": "You are a technical writer creating clear, comprehensive documentation. Write in an educational, accessible style.",
            },
            {"role": "user", "content": prompt},
        ]

        return self._call_api(messages, max_tokens=4096)
