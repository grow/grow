"""Test the profiling timer"""

import unittest
import mock
from . import profile

class TimerTestCase(unittest.TestCase):
    """Tests for the Timer"""

    def setUp(self):
        self.profile = profile.Profile()

    def test_timer(self):
        """Test timer."""

        timer = self.profile.timer('test')
        mock_time = mock.Mock()
        mock_time.time.side_effect = [0, 10]

        # pylint: disable=protected-access
        timer._time = mock_time

        with timer:
            pass

        self.assertEqual([{
            'key': 'test',
            'label': 'test',
            'meta': None,
            'start': 0,
            'end': 10,
        }], self.profile.export())


if __name__ == '__main__':
    unittest.main()
