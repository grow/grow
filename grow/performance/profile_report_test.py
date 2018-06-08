"""Test the profiling report"""

import unittest
import mock
from grow.performance import profile
from grow.performance import profile_report


class TimerReportTestCase(unittest.TestCase):
    """Tests for the TimerReport"""

    def _add_timer(self, key, start=0, end=10):
        timer = profile.Timer(key)
        timer.start = start
        timer.end = end
        self.profile.add_timer(timer)

    def setUp(self):
        self.profile = profile.Profile()

    def test_analyze(self):
        """Test empty analyze."""
        report = profile_report.ProfileReport(self.profile)
        self.assertEqual(None, report.analyze())

    def test_export_empty(self):
        """Test empty report."""
        report = profile_report.ProfileReport(self.profile)
        self.assertEqual({}, report.export())

    def test_export_single_timer(self):
        """Test report with timer."""
        self._add_timer('a', start=1, end=3)
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

    def test_export_grouped_timers(self):
        """Test report with similar timer keys."""
        self._add_timer('a', start=1, end=3)
        self._add_timer('a', start=2, end=5)
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

    def test_export_multiple_timers(self):
        """Test report with similar timer keys."""
        self._add_timer('a', start=1, end=3)
        self._add_timer('b', start=2, end=5)
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

    def test_pretty_print(self):
        """Test that pretty print is working correctly."""
        self._add_timer('a', start=1, end=3)
        report = profile_report.ProfileReport(self.profile)
        mock_print = mock.Mock()
        report.pretty_print(print_func=mock_print)
        mock_print.assert_called_with('a (1): Avg 2.0 Min 2 Max 2')

    def test_pretty_print_multiple(self):
        """Test that pretty print is working correctly."""
        self._add_timer('a', start=1, end=3)
        self._add_timer('a', start=2, end=7)
        report = profile_report.ProfileReport(self.profile)
        mock_print = mock.Mock()
        report.pretty_print(print_func=mock_print)
        calls = [
            mock.call('a (2): Avg 3.5 Min 2 Max 5'),
            mock.call('<Timer key=a duration=5>'),
            mock.call('<Timer key=a duration=2>'),
        ]
        mock_print.assert_has_calls(calls)


if __name__ == '__main__':
    unittest.main()
