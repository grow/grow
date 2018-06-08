"""Test the profiling report"""

import unittest
from . import profile
from . import profile_report


class TimerReportTestCase(unittest.TestCase):
    """Tests for the TimerReport"""

    def setUp(self):
        self.profile = profile.Profile()
        self.report = profile_report.ProfileReport(self.profile)

    def test_analyze_empty(self):
        """Test report."""
        self.assertEqual(None, self.report.analyze())


if __name__ == '__main__':
    unittest.main()
