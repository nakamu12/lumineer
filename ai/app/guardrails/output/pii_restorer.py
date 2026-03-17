"""L4 Output Guard: Restore PII placeholders to original values.

After the LLM generates a response using masked input,
this module replaces placeholders (e.g. <EMAIL_ADDRESS>) with
the original PII values before returning to the user.

Note: PiiMapping is defined here to avoid a circular dependency
with pii_sanitizer (L1 input guard). Both modules use the same
dataclass shape.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PiiMapping:
    """Maps a masked placeholder back to its original PII value."""

    original: str
    masked: str
    entity_type: str


def restore_pii(text: str, mappings: tuple[PiiMapping, ...]) -> str:
    """Replace masked placeholders with original PII values."""
    if not mappings:
        return text

    result = text
    for mapping in mappings:
        result = result.replace(mapping.masked, mapping.original)
    return result
