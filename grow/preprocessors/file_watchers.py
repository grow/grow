from . import translation
from watchdog import events
from watchdog import observers
from xtermcolor import colorize


class PodFileEventHandler(events.PatternMatchingEventHandler):
    patterns = ['*']
    ignore_directories = True

    def __init__(self, pod, managed_observer, *args, **kwargs):
        self.pod = pod
        self.managed_observer = managed_observer
        super(PodFileEventHandler, self).__init__(*args, **kwargs)

    def handle(self, event=None):
        pod_path = event.src_path[len(self.pod.root):]
        self.pod.on_file_changed(pod_path)
        self.managed_observer.reschedule_children()

    def on_created(self, event):
        self.handle(event)

    def on_modified(self, event):
        self.handle(event)


class PreprocessorEventHandler(events.PatternMatchingEventHandler):
    num_runs = 0

    def __init__(self, preprocessor, *args, **kwargs):
        self.preprocessor = preprocessor
        super(PreprocessorEventHandler, self).__init__(*args, **kwargs)

    def handle(self, event=None):
        if event is not None and event.is_directory:
            return
        try:
            if self.num_runs == 0:
                self.preprocessor.first_run()
            else:
                self.preprocessor.run()
        except Exception:
            # Avoid an inconsistent state where preprocessor doesn't run again
            # if it encounters an exception. https://github.com/grow/grow/issues/81
            text = colorize('Preprocessor error.', ansi=197)
            self.preprocessor.pod.logger.exception(text)
        self.num_runs += 1

    def on_created(self, event):
        self.handle(event)

    def on_modified(self, event):
        self.handle(event)


class ManagedObserver(observers.Observer):

    def __init__(self, pod):
        self.pod = pod
        self._preprocessor_watches = []
        self._child_observers = []
        super(ManagedObserver, self).__init__()

    def schedule_podfile(self):
        podfile_handler = PodFileEventHandler(self.pod, managed_observer=self)
        self.schedule(podfile_handler, path=self.pod.root, recursive=True)

    def schedule_builtins(self):
        preprocessor = translation.TranslationPreprocessor(pod=self.pod)
        self._schedule_preprocessor('/translations/', preprocessor, patterns=['*.po'])

    def schedule_preprocessors(self):
        self._preprocessor_watches = []
        for preprocessor in self.pod.list_preprocessors():
            for path in preprocessor.list_watched_dirs():
                watch = self._schedule_preprocessor(path, preprocessor)
                if watch:
                    self._preprocessor_watches.append(watch)

    def _schedule_preprocessor(self, path, preprocessor, **kwargs):
        try:
            if 'ignore_directories' in kwargs:
                kwargs['ignore_directories'] = [self.pod.abs_path(p)
                                                for p in kwargs['ignore_directories']]
            path = self.pod.abs_path(path)
            handler = PreprocessorEventHandler(preprocessor, **kwargs)
            return self.schedule(handler, path=path, recursive=True)
        except OSError:
            # No directory found.
            return None

    def reschedule_children(self):
        for observer in self._child_observers:
            for watch in observer._preprocessor_watches:
                observer.unschedule(watch)
            observer.schedule_preprocessors()

    def add_child(self, observer):
        self._child_observers.append(observer)
        return observer

    def start(self):
        for observer in self._child_observers:
            observer.start()
        super(ManagedObserver, self).start()

    def stop(self):
        for observer in self._child_observers:
            observer.stop()
        super(ManagedObserver, self).stop()

    def join(self):
        for observer in self._child_observers:
            observer.join()
        super(ManagedObserver, self).join()

    def run_handlers(self):
        for handlers in self._handlers.values():
            for handler in handlers:
                handler.handle()


def create_dev_server_observers(pod):
    main_observer = ManagedObserver(pod)
    main_observer.schedule_builtins()
    main_observer.schedule_preprocessors()

    podspec_observer = ManagedObserver(pod)
    podspec_observer.schedule_podfile()
    podspec_observer.add_child(main_observer)
    podspec_observer.start()
    return main_observer, podspec_observer
