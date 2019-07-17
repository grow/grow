"""Test the logger."""

import unittest
from grow.common import logger as grow_logger


class LoggerCase(unittest.TestCase):
    """Tests for the Logger"""

    def test_init(self):
        """Init with value correctly uses value."""
        logger = grow_logger.Logger(logger='test')
        self.assertEqual('test', logger.logger)

    def test_init_default(self):
        """Init with no value correctly uses global logger."""
        logger = grow_logger.Logger()
        self.assertEqual(logger.logger, grow_logger.LOGGER)


if __name__ == '__main__':
    unittest.main()
