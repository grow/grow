"""Lightweight ASCII table renderer (replaces texttable-fixed)."""

import re
import textwrap

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


class bcolors:
    """ANSI terminal color codes compatible with texttable.bcolors."""

    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'


def get_color_string(color, text):
    """Wrap text in an ANSI color sequence."""
    return f'{color}{text}{bcolors.ENDC}'


def _visible_len(text):
    return len(_ANSI_RE.sub('', text))


def _pad(text, width, align):
    pad = max(0, width - _visible_len(text))
    if align == 'r':
        return (' ' * pad) + text
    if align == 'c':
        left = pad // 2
        return (' ' * left) + text + (' ' * (pad - left))
    return text + (' ' * pad)


class Texttable:
    """Simple ASCII table formatter supporting header separator, alignment, and wrapping."""

    BORDER = 1
    HEADER = 2
    HLINES = 4
    VLINES = 8

    def __init__(self, max_width=80):
        self._max_width = max_width
        self._deco = self.BORDER | self.HEADER | self.HLINES | self.VLINES
        self._header = []
        self._rows = []
        self._align = []
        self._dtype = []

    def set_deco(self, deco):
        self._deco = deco

    def set_cols_align(self, array):
        self._align = list(array)

    def set_cols_dtype(self, array):
        self._dtype = list(array)

    def add_rows(self, rows, header=True):
        rows = list(rows)
        if not rows:
            return
        if header:
            self._header = [self._format_cell(c, i) for i, c in enumerate(rows[0])]
            rows = rows[1:]
        for row in rows:
            self._rows.append([self._format_cell(c, i) for i, c in enumerate(row)])

    def _format_cell(self, value, col_idx):
        if value is None:
            return ''
        dtype = self._dtype[col_idx] if col_idx < len(self._dtype) else 'a'
        if dtype == 'i':
            try:
                return str(int(value))
            except (TypeError, ValueError):
                return str(value)
        return str(value)

    def _compute_widths(self, all_rows, num_cols):
        widths = [0] * num_cols
        for row in all_rows:
            for i in range(min(num_cols, len(row))):
                for line in row[i].splitlines() or ['']:
                    widths[i] = max(widths[i], _visible_len(line))

        if self._max_width and self._max_width > 0:
            sep_width = 3 * max(0, num_cols - 1)
            available = max(num_cols, self._max_width - sep_width)
            total = sum(widths)
            if total > available:
                # Shrink widest columns proportionally while keeping a minimum width of 4.
                while sum(widths) > available:
                    widest = max(range(num_cols), key=lambda i: widths[i])
                    if widths[widest] <= 4:
                        break
                    widths[widest] -= 1
        return widths

    def _wrap_row(self, row, widths):
        wrapped_cols = []
        for i, width in enumerate(widths):
            cell = row[i] if i < len(row) else ''
            lines = []
            for raw_line in cell.splitlines() or ['']:
                if self._max_width and self._max_width > 0 and _visible_len(raw_line) > width:
                    lines.extend(textwrap.wrap(raw_line, width=max(1, width)) or [''])
                else:
                    lines.append(raw_line)
            wrapped_cols.append(lines)
        height = max((len(col) for col in wrapped_cols), default=1)
        out_lines = []
        for line_idx in range(height):
            parts = []
            for col_idx, width in enumerate(widths):
                col_lines = wrapped_cols[col_idx]
                text = col_lines[line_idx] if line_idx < len(col_lines) else ''
                align = self._align[col_idx] if col_idx < len(self._align) else 'l'
                parts.append(_pad(text, width, align))
            out_lines.append('   '.join(parts))
        return out_lines

    def draw(self):
        all_rows = ([self._header] if self._header else []) + self._rows
        if not all_rows:
            return ''
        num_cols = max(len(r) for r in all_rows)
        widths = self._compute_widths(all_rows, num_cols)
        lines = []
        if self._header:
            lines.extend(f'{line} ' for line in self._wrap_row(self._header, widths))
            if self._deco & self.HEADER:
                total_width = sum(widths) + 3 * max(0, num_cols - 1)
                lines.append('=' * total_width)
        for row in self._rows:
            lines.extend(self._wrap_row(row, widths))
        return '\n'.join(lines)
