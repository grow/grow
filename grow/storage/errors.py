class Error(Exception):
    pass


class PathError(Error, ValueError):
    pass


class NotFoundError(Error, IOError):
    pass
