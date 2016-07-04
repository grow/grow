import datetime
from . import base


class RoutesCachePreprocessor(base.BasePreprocessor):
    KIND = '_routes_cache'
    LIMIT = datetime.timedelta(seconds=1)

    def __init__(self, pod):
        self.pod = pod
        self._last_run = None

    def run(self, build=True):
        # Avoid rebuilding routes cache more than once per second.
        now = datetime.datetime.now()
        limit = RoutesCachePreprocessor.LIMIT
        if not self._last_run or (now - self._last_run) > limit:
            self.pod.routes.reset_cache(rebuild=True, inject=False)
            self._last_run = now

    def list_watched_dirs(self):
        return ['/content/']
