"""Logging utilities for grow."""

import logging

def get_logger(name='pod'):
    """Creates a logger with formatting and a stream handler."""
    handler = logging.StreamHandler()
    _formatter = logging.Formatter('[%(asctime)s] %(message)s', '%H:%M:%S')
    handler.setFormatter(_formatter)
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.addHandler(handler)
    return logger

LOGGER = get_logger('pod')
