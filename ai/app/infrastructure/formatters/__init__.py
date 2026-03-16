"""Context formatter strategy implementations."""

from app.infrastructure.formatters.base import BaseFormatter
from app.infrastructure.formatters.json_formatter import JsonFormatter
from app.infrastructure.formatters.toon_formatter import ToonFormatter

__all__ = ["BaseFormatter", "JsonFormatter", "ToonFormatter"]


def create_formatter(fmt: str) -> BaseFormatter:
    """Factory: create formatter from format name ('json' | 'toon')."""
    match fmt:
        case "json":
            return JsonFormatter()
        case "toon":
            return ToonFormatter()
        case _:
            raise ValueError(f"Unknown formatter: {fmt!r}")
