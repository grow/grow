from grow.pods import messages


class Error(Exception):
  pass


class FileDoesNotExistError(Error):
  pass


class File(object):

  def __init__(self, pod_path, pod):
    self.pod_path = pod_path
    self.pod = pod

  @classmethod
  def list(cls, pod, prefix='/'):
    paths = pod.list_dir(prefix)
    return [File(path, pod) for path in paths]

  def get_content(self):
    try:
      return self.pod.read_file(self.pod_path)
    except IOError as e:
      raise FileDoesNotExistError(e)

  def update_content(self, content):
    if isinstance(content, unicode):
      content = content.encode('utf-8')
    self.pod.write_file(self.pod_path, content)

  def to_message(self):
    message = messages.FileMessage()
    message.pod_path = self.pod_path
    message.content = self.get_content()
    return message
