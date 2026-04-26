"""Compatibility helpers for cross-version Python support."""

from __future__ import annotations

from dataclasses import dataclass as _stdlib_dataclass
from typing import Any


def compat_dataclass(_cls: type[Any] | None = None, **kwargs: Any):
    """Wrap dataclass to gracefully handle Python versions without slots support."""

    def _decorate(cls: type[Any]):
        try:
            return _stdlib_dataclass(cls, **kwargs)
        except TypeError as exc:
            if "unexpected keyword argument 'slots'" not in str(exc):
                raise
            fallback_kwargs = dict(kwargs)
            fallback_kwargs.pop("slots", None)
            return _stdlib_dataclass(cls, **fallback_kwargs)

    if _cls is not None:
        return _decorate(_cls)
    return _decorate
