"""Profiling report for analyizing the performance of the app"""


class ProfileReport(object):
    """Analyzes the timers to report on the app timing."""

    def __init__(self, profile):
        self.profile = profile
        self.items = {}

        for timer in self.profile:
            if timer.key not in self.items:
                self.items[timer.key] = ReportItem(timer.key)
            self.items[timer.key].add_timer(timer)

    def analyze(self):
        """Performs an analysis of the timers."""
        pass

    def export(self):
        """Export the timer data for each timer."""
        exported = {}
        for key, item in self.items.iteritems():
            exported[key] = item.export()
        return exported

    def pretty_print(self):
        """Prints out the report in a nice format."""
        for _, item in self.items.iteritems():
            print '{} ({}): Avg {} Min {} Max {} '.format(
                item.key, len(item), item.average_duration, item.min_duration, item.max_duration)
            if len(item) > 1:
                for timer in item.top():
                    print timer


class ReportItem(object):
    """Report item used to store information about all timers with the same key."""

    def __init__(self, key):
        self.key = key
        self.timers = []
        self.start = None
        self.end = None

    def __len__(self):
        return len(self.timers)

    @property
    def average_duration(self):
        """Calculate the average duration of the timers."""
        duration_sum = 0
        for timer in self.timers:
            duration_sum = duration_sum + timer.duration
        return duration_sum / len(self.timers)

    @property
    def max_duration(self):
        """Calculate the maximum duration of the timers."""
        value = None
        for timer in self.timers:
            if not value or value < timer.duration:
                value = timer.duration
        return value

    @property
    def min_duration(self):
        """Calculate the minimum duration of the timers."""
        value = None
        for timer in self.timers:
            if not value or value > timer.duration:
                value = timer.duration
        return value

    @property
    def duration(self):
        """Duration of timers."""
        return self.end - self.start

    def add_timer(self, timer):
        """Add a timer to the report item to track it."""
        self.timers.append(timer)

        # Keep track of the first start and last end time.
        if not self.start or timer.start < self.start:
            self.start = timer.start
        if not self.end or timer.end > self.end:
            self.end = timer.end

    def export(self):
        """Export the timer data for each timer."""
        return {
            'start': self.start,
            'end': self.end,
            'timers': [t.export() for t in self.timers],
        }

    def top(self, count=5, ascending=False):
        """Get the top (or bottom) timers by duration."""
        top_list = sorted(self.timers, key=lambda k: k.duration)
        if not ascending:
            top_list.reverse()
        return top_list[:count]
