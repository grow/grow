class Error(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class NotFoundError(Error, IOError):
    pass


class NoCatalogsError(Error):
    """Error when no catalogs are found for translations."""
