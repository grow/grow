class Error(Exception):
    pass


class NotFoundError(Error, IOError):
    pass


class NoCatalogsError(Error):
    """Error when no catalogs are found for translations."""
    pass
