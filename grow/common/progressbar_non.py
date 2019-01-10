"""Non-interactive progressbar fallback for non-interactive shells."""

import os
import sys
import datetime
import progressbar


class NonInteractiveProgressBar(object):
    """Non-interactive stub version of progress bar."""

    def __init__(self, message, max_value=None, poll_interval=5, widgets=None, *_args, **kwargs):
        self._last_print = datetime.datetime.now()
        self._last_update = datetime.datetime.now()
        self._min_delta = datetime.timedelta(0, poll_interval)
        self._max_value = max_value
        self._widgets = widgets or []
        self._data = kwargs
        self._started_on = None
        self._finished_on = None
        self._value = 0

        print message

    @property
    def percentage(self):
        """Percentage of value vs max_value."""
        if not self._max_value:
            return None
        return self._value / self._max_value

    @property
    def value(self):
        """Value of the progress bar."""
        return self._value

    def data(self):
        """Try to mimic the data available to the progressbar."""
        elapsed = self._last_update - self._started_on
        return dict(
            # The maximum value (can be None with iterators)
            max_value=self._max_value,
            # Start time of the widget
            start_time=self._started_on,
            # Last update time of the widget
            last_update_time=self._last_update,
            # End time of the widget
            end_time=self._finished_on,
            # The current value
            value=self._value,
            # The seconds since the bar started
            total_seconds_elapsed=elapsed.total_seconds,
            # The seconds since the bar started modulo 60
            seconds_elapsed=(elapsed.seconds % 60) +
            (elapsed.microseconds / 1000000.),
            # The minutes since the bar started modulo 60
            minutes_elapsed=(elapsed.seconds / 60) % 60,
            # The hours since the bar started modulo 24
            hours_elapsed=(elapsed.seconds / (60 * 60)) % 24,
            # The hours since the bar started
            days_elapsed=(elapsed.seconds / (60 * 60 * 24)),
            # The raw elapsed `datetime.timedelta` object
            time_elapsed=elapsed,
            # Percentage as a float or `None` if no max_value is available
            percentage=self.percentage,
        )

    def finish(self):
        """Finished with the progressbar."""
        self._finished_on = datetime.datetime.now()
        for widget in self._widgets:
            print widget(self, self.data())

    def start(self):
        """Started with the progressbar."""
        self._started_on = datetime.datetime.now()

    def update(self, value):
        self._last_update = datetime.datetime.now()
        self._value = value
        if self._last_update - self._last_print > self._min_delta:
            for widget in self._widgets:
                print widget(self, self.data())
            self._last_print = self._last_update


def create_progressbar(message, *args, **kwargs):
    """Create the correct progressbar based on availability of interactive shell."""
    if 'CI' in os.environ and os.environ['CI']:
        kwargs['poll_interval'] = 10
    return progressbar.ProgressBar(*args, **kwargs)
    # Removing for now to see if it is causing an issue with
    # if hasattr(sys.stdout, 'fileno') and os.isatty(sys.stdout.fileno()):
    #     return progressbar.ProgressBar(*args, **kwargs)
    # return NonInteractiveProgressBar(message, *args, **kwargs)
