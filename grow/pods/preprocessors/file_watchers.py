from grow.pods.preprocessors import translation as translation_preprocessor
from watchdog import events
from watchdog import observers


class PodspecFileEventHandler(events.PatternMatchingEventHandler):
  patterns = ['*/podspec.yaml']
  ignore_directories = True

  def __init__(self, pod, managed_observer, *args, **kwargs):
    self.pod = pod
    self.managed_observer = managed_observer
    super(PodspecFileEventHandler, self).__init__(*args, **kwargs)

  def _handle(self, event):
    print len(self.managed_observer._preprocessor_watches)
    self.managed_observer.reschedule_preprocessors()
    print len(self.managed_observer._preprocessor_watches)

  def on_created(self, event):
    self._handle(event)

  def on_modified(self, event):
    self._handle(event)


class PreprocessorEventHandler(events.FileSystemEventHandler):

  def __init__(self, preprocessor, *args, **kwargs):
    self.preprocessor = preprocessor
    super(PreprocessorEventHandler, self).__init__(*args, **kwargs)

  def on_modified(self, event):
    print event.src_path
    print event.event_type
    print 'modified', event


class ManagedObserver(observers.Observer):

  def __init__(self, pod):
    self.pod = pod
    self._preprocessor_watches = []
    super(ManagedObserver, self).__init__()

  def schedule_podspec(self):
    podspec_handler = PodspecFileEventHandler(self.pod, managed_observer=self)
    self.schedule(podspec_handler, path=self.pod.root, recursive=False)

  def schedule_translation(self):
    preprocessor = translation_preprocessor.TranslationPreprocessor(pod=self.pod)
    self._schedule_preprocessor('/translations/', preprocessor)

  def schedule_preprocessors(self):
    for preprocessor in self.pod.list_preprocessors():
      for path in preprocessor.list_watched_dirs():
        watch = self._schedule_preprocessor(path, preprocessor)
        self._preprocessor_watches.append(watch)

  def _schedule_preprocessor(self, path, preprocessor):
    path = self.pod.abs_path(path)
    handler = PreprocessorEventHandler(preprocessor)
    return self.schedule(handler, path=path, recursive=True)

  def reschedule_preprocessors(self):
    self.stop()
    for watch in self._preprocessor_watches:
      self.unschedule(watch)
    self.schedule_preprocessors()
    self.start()
    print 'done'
