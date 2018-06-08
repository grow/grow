"""Test the profiling report"""

import unittest
from . import profile
from . import profile_report


class TimerReportTestCase(unittest.TestCase):
    """Tests for the TimerReport"""

    def setUp(self):
        self.profile = profile.Profile()

    def test_analyze_empty(self):
        """Test empty report."""
        report = profile_report.ProfileReport(self.profile)
        self.assertEqual({}, report.export())

    def test_single_timer(self):
        """Test report with timer."""
        timer = profile.Timer('a')
        timer.start = 1
        timer.end = 3
        self.profile.add_timer(timer)
        report = profile_report.ProfileReport(self.profile)
        self.assertEqual({
            'a': {
                'end': 3,
                'start': 1,
                'timers': [
                    {
                        'end': 3,
                        'key': 'a',
                        'label': 'a',
                        'meta': None,
                        'start': 1
                    },
                ]
            },
        }, report.export())

    def test_grouped_timers(self):
        """Test report with similar timer keys."""
        timer = profile.Timer('a')
        timer.start = 1
        timer.end = 3
        self.profile.add_timer(timer)
        timer = profile.Timer('a')
        timer.start = 2
        timer.end = 5
        self.profile.add_timer(timer)
        report = profile_report.ProfileReport(self.profile)
        self.assertEqual({
            'a': {
                'end': 5,
                'start': 1,
                'timers': [
                    {
                        'end': 3,
                        'key': 'a',
                        'label': 'a',
                        'meta': None,
                        'start': 1
                    },
                    {
                        'end': 5,
                        'key': 'a',
                        'label': 'a',
                        'meta': None,
                        'start': 2
                    },
                ]
            },
        }, report.export())

    def test_multiple_timers(self):
        """Test report with similar timer keys."""
        timer = profile.Timer('a')
        timer.start = 1
        timer.end = 3
        self.profile.add_timer(timer)
        timer = profile.Timer('b')
        timer.start = 2
        timer.end = 5
        self.profile.add_timer(timer)
        report = profile_report.ProfileReport(self.profile)
        self.assertEqual({
            'a': {
                'end': 3,
                'start': 1,
                'timers': [
                    {
                        'end': 3,
                        'key': 'a',
                        'label': 'a',
                        'meta': None,
                        'start': 1
                    },
                ]
            },
            'b': {
                'end': 5,
                'start': 2,
                'timers': [
                    {
                        'end': 5,
                        'key': 'b',
                        'label': 'b',
                        'meta': None,
                        'start': 2
                    },
                ]
            },
        }, report.export())


if __name__ == '__main__':
    unittest.main()
