"""Test the profiling timer"""

import unittest
import mock
from grow.performance import profile

class TimerTestCase(unittest.TestCase):
    """Tests for the Timer"""

    def setUp(self):
        self.mock_time = mock.Mock()
        self.mock_time.time.side_effect = [0, 10]
        self.profile = profile.Profile()

    def test_add_timer(self):
        """Test adding timer."""

        timer = profile.Timer('test')

        # pylint: disable=protected-access
        timer._time = self.mock_time

        with timer:
            pass

        self.assertEqual(0, len(self.profile))
        self.profile.add_timer(None)
        self.assertEqual(0, len(self.profile))
        self.profile.add_timer(timer)
        self.assertEqual(1, len(self.profile))
        self.assertIn(timer, list(self.profile))

    def test_callable(self):
        """Test adding timer by calling the profiler."""

        timer = self.profile('test')
        self.assertEqual(1, len(self.profile))
        self.assertIn(timer, list(self.profile))

    def test_timer(self):
        """Test timer."""

        timer = self.profile.timer('test')

        # pylint: disable=protected-access
        timer._time = self.mock_time

        with timer:
            pass

        self.assertEqual([{
            'key': 'test',
            'label': 'test',
            'meta': None,
            'start': 0,
            'end': 10,
        }], self.profile.export())

    def test_repr(self):
        """Repr of timer"""
        timer = self.profile.timer('test')

        # pylint: disable=protected-access
        timer._time = self.mock_time

        with timer:
            pass

        self.assertEqual('<Timer key=test duration=10>', repr(timer))

        timer.label = 'foobar'
        self.assertEqual('<Timer key=test label=foobar duration=10>', repr(timer))


class ProfilerCase(unittest.TestCase):
    """Tests for the Timer"""

    def test_init(self):
        """Init with value correctly uses value."""
        profiler = profile.Profiler(profiler='test')
        self.assertEqual('test', profiler.profiler)

    def test_init_default(self):
        """Init with no value correctly uses creates new profiler."""
        profiler = profile.Profiler()
        self.assertIsInstance(profiler.profiler, profile.Profile)


if __name__ == '__main__':
    unittest.main()
