from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pipeline.sources.base import BaseSource

_REGISTRY: dict[str, type[BaseSource]] = {}


def register_source(cls: type[BaseSource]) -> type[BaseSource]:
    """Class decorator that registers a source by its get_source_name() value.

    Uses __new__ to avoid requiring constructor args at decoration time
    (constructor args come from SOURCE_CONFIGS at runtime, not at import time).
    Triggered automatically when the source module is imported in __init__.py.
    """
    instance = cls.__new__(cls)
    name = cls.get_source_name(instance)
    _REGISTRY[name] = cls
    return cls


def get_source(name: str, **kwargs) -> BaseSource | None:
    """Factory: look up a registered source class by name and instantiate it.

    kwargs are source-specific config (API keys, etc.) from SOURCE_CONFIGS.
    Returns None if no source is registered under the given name.
    """
    cls = _REGISTRY.get(name)
    if cls is None:
        return None
    return cls(**kwargs)


def available_sources() -> list[str]:
    """Return all registered source names (useful for validation / UI dropdowns)."""
    return list(_REGISTRY.keys())
