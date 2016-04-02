from . import base


class RoutesCachePreprocessor(base.BasePreprocessor):
    KIND = '_routes_cache'

    def __init__(self, pod):
        self.pod = pod

    def run(self, build=True):
        self.pod.routes.reset_cache(rebuild=True)

    def list_watched_dirs(self):
        return ['/content/', '/static/']
