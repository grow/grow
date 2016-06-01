from twisted.internet import reactor
import os
import time


class Error(Exception):
    pass


class PreprocessorError(Error):
    pass


class BasePreprocessor(object):

    def __init__(self, pod, config, autorun=True, name=None, tags=None,
                 schedule=None):
        self.pod = pod
        self.root = pod.root
        self.config = config
        self.logger = self.pod.logger
        self.autorun = autorun
        self.name = name
        self.tags = tags or []
        self.schedule = schedule

    def first_run(self):
        self.run()

    def run(self, build=True):
        raise NotImplementedError

    def list_watched_dirs(self):
        return []

    def normalize_path(self, path):
        if path.startswith('/'):
            return os.path.join(self.root, path.lstrip('/'))
        return path

    def run_with_schedule(self):
        if not self.schedule:
            return
        # TODO(jeremydw): Actually parse the "schedule" parameter.
        # For now, this is hardcoded to every 10 seconds as a demo.
        scheduled_ratelimit = 10
        def _scheduled_run():
            while True:
                self.run()
                time.sleep(scheduled_ratelimit)
        # TODO(jeremydw): This doesn't seem to clean up the threads properly
        # when ctrl+c is invoked.
        reactor.callInThread(_scheduled_run)
