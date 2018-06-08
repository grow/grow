"""Custom formatting utilities."""

import string
from grow.common import structures


FORMATTER = string.Formatter()


def safe_format(base_string, *args, **kwargs):
    """Safely format a string using the modern string formatting with fallback."""
    safe_kwargs = structures.SafeDict(**kwargs)
    return FORMATTER.vformat(base_string, args, safe_kwargs)
