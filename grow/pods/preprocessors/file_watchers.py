from grow.pods.preprocessors import translation as translation_preprocessor
import threading
from watchdog import events
from watchdog import observers


class PodspecFileEventHandler(events.PatternMatchingEventHandler):
  patterns = ['*/podspec.yaml']
  ignore_directories = True

  def __init__(self, pod, managed_observer, *args, **kwargs):
    self.pod = pod
    self.managed_observer = managed_observer
    super(PodspecFileEventHandler, self).__init__(*args, **kwargs)

  def handle(self, event=None):
    self.managed_observer.reschedule_children()

  def on_created(self, event):
    self.handle(event)

  def on_modified(self, event):
    self.handle(event)


class PreprocessorEventHandler(events.FileSystemEventHandler):
  num_runs = 0

  def __init__(self, preprocessor, *args, **kwargs):
    self.preprocessor = preprocessor
    super(PreprocessorEventHandler, self).__init__(*args, **kwargs)

  def handle(self, event=None):
    if event is not None and event.is_directory:
      return
    if self.num_runs == 0:
      self.preprocessor.first_run()
    else:
      self.preprocessor.run()
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

  def schedule_podspec(self):
    podspec_handler = PodspecFileEventHandler(self.pod, managed_observer=self)
    self.schedule(podspec_handler, path=self.pod.root, recursive=False)

  def schedule_translation(self):
    preprocessor = translation_preprocessor.TranslationPreprocessor(pod=self.pod)
    self._schedule_preprocessor('/translations/', preprocessor)

  def schedule_preprocessors(self):
    self._preprocessor_watches = []
    for preprocessor in self.pod.list_preprocessors():
      for path in preprocessor.list_watched_dirs():
        watch = self._schedule_preprocessor(path, preprocessor)
        self._preprocessor_watches.append(watch)

  def _schedule_preprocessor(self, path, preprocessor):
    path = self.pod.abs_path(path)
    handler = PreprocessorEventHandler(preprocessor)
    return self.schedule(handler, path=path, recursive=True)

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


def create_dev_server_observer(pod):
  main_observer = ManagedObserver(pod)
  main_observer.schedule_translation()
  main_observer.schedule_preprocessors()
  thread = threading.Thread(target=main_observer.run_handlers)
  thread.start()

  podspec_observer = ManagedObserver(pod)
  podspec_observer.schedule_podspec()
  podspec_observer.add_child(main_observer)
  podspec_observer.start()
  return podspec_observer
