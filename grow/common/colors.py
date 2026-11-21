"""Colors for use in logging."""

# ANSI 256-color escape sequences that look good on both black and white backgrounds.
_RESET = '\x1b[0m'
CAUTION = '\x1b[38;5;3m\x1b[1m'
EMPHASIS = '\x1b[38;5;130m'
ERROR = '\x1b[38;5;1m\x1b[1m'
HIGHLIGHT = '\x1b[38;5;10m'
SUCCESS = '\x1b[38;5;2m\x1b[1m'


def stylize(text, styles, reset=True):
    """Apply ANSI color/style codes to text."""
    prefix = ''.join(styles) if isinstance(styles, (list, tuple)) else styles
    suffix = _RESET if reset else ''
    return f'{prefix}{text}{suffix}'
