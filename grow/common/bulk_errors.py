"""Bulk error handling and reporting."""

import logging
import traceback

class BulkErrors(Exception):
    """Base bulk errors."""

    def __init__(self, message, errors):
        super(BulkErrors, self).__init__(message)
        self.errors = errors

def display_bulk_errors(bulk_errors):
    """Nicely log and show the bulk errors."""
    for error in bulk_errors.errors:
        logging.error(error.message)
        logging.error(error.err.message)
        traceback.print_tb(error.err_tb)
        logging.info('')
    logging.error(bulk_errors.message)
