"""Disabled placeholder for future web search integration."""

from __future__ import annotations

from ruby.core.errors import ProviderError
from ruby.providers.search.base import SearchProvider


class WebSearchPlaceholderProvider(SearchProvider):
    """Placeholder provider kept disabled in v1."""

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled

    def search(self, query: str) -> str:
        if not self.enabled:
            raise ProviderError(
                "Web search is not available in v1. This provider is intentionally disabled."
            )
        raise ProviderError("Web search placeholder has no runtime implementation yet.")
