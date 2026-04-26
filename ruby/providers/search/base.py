"""Search provider interface for future extensions."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SearchProvider(ABC):
    """Search provider contract (disabled in v1)."""

    @abstractmethod
    def search(self, query: str) -> str:
        """Execute search and return summarized results."""
