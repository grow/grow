"""Lightweight terminal progress bar (replaces progressbar2)."""

import datetime
import os
import sys
import time


class FormatLabel:
    """Format string widget supporting %(value)d and %(elapsed)s placeholders."""

    def __init__(self, format_str):
        self._format_str = format_str

    def __call__(self, _bar, data):
        return self._format_str % data


class ProgressBar:
    """Simple progress bar supporting interactive TTY and CI/non-interactive output."""

    def __init__(
        self, maxval=None, max_value=None, widgets=None, poll_interval=0.1, stream=None, **_kwargs
    ):
        self._max_value = max_value if max_value is not None else maxval
        self._widgets = widgets or []
        self._poll_interval = poll_interval
        self._stream = stream or sys.stderr
        self._started_on = None
        self._last_render = 0.0
        self._value = 0

    @property
    def value(self):
        return self._value

    @property
    def percentage(self):
        if not self._max_value:
            return None
        return (self._value / self._max_value) * 100.0

    def _is_tty(self):
        return hasattr(self._stream, 'isatty') and self._stream.isatty()

    def _data(self):
        now = datetime.datetime.now()
        elapsed = now - (self._started_on or now)
        total_secs = int(elapsed.total_seconds())
        hours, rem = divmod(total_secs, 3600)
        minutes, seconds = divmod(rem, 60)
        tenths = elapsed.microseconds // 100000
        return {
            'value': self._value,
            'max_value': self._max_value,
            'elapsed': f'{hours}:{minutes:02d}:{seconds:02d}.{tenths}',
            'time_elapsed': elapsed,
            'percentage': self.percentage or 0.0,
        }

    def _render(self, final=False):
        if not self._widgets:
            return
        data = self._data()
        text = ''.join(w(self, data) if callable(w) else str(w) for w in self._widgets)
        if self._is_tty():
            end = '\n' if final else ''
            self._stream.write(f'\r{text}{end}')
        elif final:
            self._stream.write(f'{text}\n')
        self._stream.flush()

    def start(self):
        self._started_on = datetime.datetime.now()
        self._last_render = time.monotonic()
        self._render()
        return self

    def update(self, value=None):
        if value is not None:
            self._value = value
        now = time.monotonic()
        if now - self._last_render >= self._poll_interval:
            self._last_render = now
            self._render()

    def finish(self):
        if self._max_value is not None:
            self._value = self._max_value
        self._render(final=True)


def create_progressbar(message, *args, **kwargs):
    """Create a ProgressBar configured for interactive or CI environments."""
    if os.environ.get('CI'):
        kwargs['poll_interval'] = 10
    return ProgressBar(*args, **kwargs)
