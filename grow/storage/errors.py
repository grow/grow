class Error(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class PathError(Error, ValueError):
    pass


class NotFoundError(Error, IOError):
    pass
