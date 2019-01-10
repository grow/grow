"""Code timing for profiling."""

import time


class Timer(object):
    """Times code to see how long it takes using a context manager."""

    def __init__(self, key, label=None, meta=None):
        self._time = time
        self.key = key
        self.label = label or key
        self.meta = meta
        self.start = None
        self.end = None

    def __enter__(self):
        return self.start_timer()

    def __exit__(self, *args):
        self.stop_timer()

    def __repr__(self):
        if self.label != self.key:
            return '<Timer:{} {} : {}>'.format(self.key, self.label, self.duration)
        return '<Timer:{} : {}>'.format(self.key, self.duration)

    @property
    def duration(self):
        """Duration of timer."""
        return self.end - self.start

    def export(self):
        """Export the timer data."""
        return {
            'key': self.key,
            'label': self.label,
            'meta': self.meta,
            'start': self.start,
            'end': self.end,
        }

    def start_timer(self):
        """Starts the timer."""
        self.start = self._time.time()
        return self

    def stop_timer(self):
        """Stops the timer."""
        self.end = self._time.time()
        return self


class Profile(object):
    """Keeps track of all of the timer usage."""

    def __init__(self):
        self.timers = []

    def __iter__(self):
        for timer in self.timers:
            yield timer

    def __len__(self):
        return len(self.timers)

    def add_timer(self, timer):
        """Adds a new timer."""
        if timer is None:
            return
        self.timers.append(timer)
        return timer

    def timer(self, *args, **kwargs):
        """Create a new timer."""
        timer = Timer(*args, **kwargs)
        self.timers.append(timer)
        return timer

    def export(self):
        """Export the timer data for each timer created."""
        return [t.export() for t in self.timers]
