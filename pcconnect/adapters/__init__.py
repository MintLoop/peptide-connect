"""Source adapter layer (Master Pack §4).

Every piece of evidence enters through an adapter that emits the canonical envelope.
The model layer never sees source-specific mechanics.
"""
from .base import SourceAdapter, canonical_url, register_adapter, get_adapter

# Importing the package registers every built-in adapter (janoshik + generics).
from . import janoshik  # noqa: F401,E402
from . import generic  # noqa: F401,E402

__all__ = ["SourceAdapter", "canonical_url", "register_adapter", "get_adapter"]
