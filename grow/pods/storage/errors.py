class Error(Exception):
  pass


class PathError(Error, ValueError):
  pass


class NotFoundError(Error, IOError):
  pass


#if cloudstorage:
#  NotFoundError = cloudstorage.NotFoundError
##  class NotFoundError(Error, IOError, cloudstorage.NotFoundError):
##    pass
#else:
