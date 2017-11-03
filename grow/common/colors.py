"""Colors for use in logging."""

import colored

# Colors and styles that look good on both black and white backgrounds.
CAUTION = colored.fg('yellow') + colored.attr("bold")
EMPHASIS = colored.fg('dark_orange_3a')
ERROR = colored.fg('red') + colored.attr("bold")
HIGHLIGHT = colored.fg('light_green')
SUCCESS = colored.fg('green') + colored.attr("bold")

# pylint: disable=invalid-name
stylize = colored.stylize
