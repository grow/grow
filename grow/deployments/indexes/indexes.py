from . import messages
import datetime
import hashlib
import logging
import threading
import texttable
from protorpc import protojson


class Error(Exception):
  pass


class CorruptIndexError(Error):
  pass


class Diff(object):

  @classmethod
  def is_empty(cls, diff):
    return not diff.adds and not diff.deletes and not diff.edits

  @classmethod
  def pretty_print(cls, diff):
    table = texttable.Texttable(max_width=0)
    table.set_deco(texttable.Texttable.HEADER)
    rows = []
    rows.append(['Action', 'Path', 'Last modified'])
    for add in diff.adds:
      label = texttable.get_color_string(texttable.bcolors.GREEN, 'Add')
      path = texttable.get_color_string(texttable.bcolors.WHITE, add.path)
      rows.append([label, path, add.modified])
    for edit in diff.edits:
      label = texttable.get_color_string(texttable.bcolors.PURPLE, 'Edit')
      path = texttable.get_color_string(texttable.bcolors.WHITE, edit.path)
      rows.append([label, path, edit.modified])
    for delete in diff.deletes:
      label = texttable.get_color_string(texttable.bcolors.RED, 'Delete')
      path = texttable.get_color_string(texttable.bcolors.WHITE, delete.path)
      rows.append([label, path, delete.modified])
    table.add_rows(rows)
    logging.info('\n' + table.draw() + '\n')


class Index(object):
  paths_to_shas = None
  modified_by = None
  modified = None

  def __init__(self):
    self.paths_to_shas = {}

  def __contains__(self, key):
    return key in self.paths_to_shas

  def __getitem__(self, key):
    return self.paths_to_shas[key]

  def __delitem__(self, key):
    del self.paths_to_shas[key]

  def iteritems(self):
    return self.paths_to_shas.iteritems()

  def update(self, paths_to_contents):
    self.paths_to_shas = {}
    for pod_path, contents in paths_to_contents.iteritems():
      pod_path = '/' + pod_path.lstrip('/')
      m = hashlib.sha1()
      if isinstance(contents, unicode):
        contents = contents.encode('utf-8')
      m.update(contents)
      self.paths_to_shas[pod_path] = m.hexdigest()
    return self.paths_to_shas

  def create_diff(self, theirs):
    diff = messages.DiffMessage()

    for path, sha in self.iteritems():
      if path in theirs:
        if self[path] == theirs[path]:
          file_message = messages.FileMessage()
          file_message.path = path
          file_message.modified = theirs.modified
          file_message.modified_by = theirs.modified_by
          diff.nochanges.append(file_message)
        else:
          file_message = messages.FileMessage()
          file_message.path = path
          file_message.modified = theirs.modified
          file_message.modified_by = theirs.modified_by
          diff.edits.append(file_message)
        del theirs[path]
      else:
        file_message = messages.FileMessage()
        file_message.path = path
        diff.adds.append(file_message)

    for path, sha in theirs.iteritems():
      file_message = messages.FileMessage()
      file_message.path = path
      file_message.modified = theirs.modified
      file_message.modified_by = theirs.modified_by
      diff.deletes.append(file_message)

    return diff

  @classmethod
  def apply_diff(cls, diff, paths_to_content, write_func, delete_func, threaded=True):
    if not threaded:
      for file_message in diff.adds:
        logging.info('Writing new file: {}'.format(file_message.path))
        content = file_message.paths_to_content[file_message.path]
        write_func(file_message.path, content)
      for file_message in diff.edits:
        logging.info('Writing changed file: {}'.format(file_message.path))
        content = file_message.paths_to_content[file_message.path]
        write_func(file_message.path, content)
      for file_message in diff.deletes:
        logging.info('Deleting file: {}'.format(file_message.path))
        delete_func(file_message.path)
      return

    # TODO(jeremydw): Thread pool for the threaded operation.
    threads = []
    for file_message in diff.adds:
      logging.info('Writing new file: {}'.format(file_message.path))
      content = paths_to_content[file_message.path]
      thread = threading.Thread(target=write_func, args=(file_message.path, content))
      threads.append(thread)
      thread.start()
    for file_message in diff.edits:
      logging.info('Writing changed file: {}'.format(file_message.path))
      content = paths_to_content[file_message.path]
      thread = threading.Thread(target=write_func, args=(file_message.path, content))
      threads.append(thread)
      thread.start()
    for file_message in diff.deletes:
      logging.info('Deleting file: {}'.format(file_message.path))
      thread = threading.Thread(target=delete_func, args=(file_message.path,))
      threads.append(thread)
      thread.start()
    for thread in threads:
      thread.join()

  def to_message(self):
    message = messages.IndexMessage()
    message.files = []
    message.modified = datetime.datetime.now()
    for path, sha in self.paths_to_shas.iteritems():
      file_message = messages.FileMessage(path=path, sha=sha)
      message.files.append(file_message)
    return message

  def to_string(self):
    return protojson.encode_message(self.to_message())

  @classmethod
  def from_message(cls, message):
    index = cls()
    index.modified = message.modified
    index.modified_by = message.modified_by
    for file_message in message.files:
      index.paths_to_shas[file_message.path] = file_message.sha
    return index

  @classmethod
  def from_string(cls, content):
    index_message = protojson.decode_message(messages.IndexMessage, content)
    return cls.from_message(index_message)
