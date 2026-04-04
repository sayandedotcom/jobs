from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pipeline.sources.base import BaseSource

_REGISTRY: dict[str, type[BaseSource]] = {}


def register_source(cls: type[BaseSource]) -> type[BaseSource]:
    instance = cls.__new__(cls)
    name = cls.get_source_name(instance)
    _REGISTRY[name] = cls
    return cls


def get_source(name: str, **kwargs) -> BaseSource | None:
    cls = _REGISTRY.get(name)
    if cls is None:
        return None
    return cls(**kwargs)


def available_sources() -> list[str]:
    return list(_REGISTRY.keys())
