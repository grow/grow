class Error(Exception):
    pass


class NotFoundError(Error, IOError):
    pass
