from . import messages
import datetime
import hashlib
import logging
import texttable
import threading
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
  def _format_author(cls, author):
    return '{} <{}>'.format(author.name, author.email) if author else ''

  @classmethod
  def _make_diff_row(cls, color, label, message):
    label = texttable.get_color_string(color, label)
    path = texttable.get_color_string(texttable.bcolors.WHITE, message.path)
    formatted_author = cls._format_author(message.modified_by)
    modified = str(message.modified).split('.')[0] if message.modified else ''
    return [label, path, modified, formatted_author]

  @classmethod
  def pretty_print(cls, diff):
    last_commit = diff.indexes[0].commit
    new_commit = diff.indexes[1].commit
    last_formatted_author = cls._format_author(last_commit.author) if last_commit else ''
    new_formatted_author = cls._format_author(new_commit.author)
    table = texttable.Texttable(max_width=0)
    table.set_deco(texttable.Texttable.HEADER)
    rows = []
    rows.append(['', 'Commit author', 'Commit sha'])
    if last_commit:
      rows.append(['Old', last_formatted_author, last_commit.sha])
    rows.append(['New', new_formatted_author, new_commit.sha])
    table.add_rows(rows)
    logging.info('\n' + table.draw() + '\n')

    last_index = diff.indexes[0]
    new_index = diff.indexes[1]
    if last_index.modified and last_index.modified_by:
      logging.info('Last deployed {} by {} <{}>'.format(
          last_index.modified, last_index.modified_by.name,
          last_index.modified_by.email))
    logging.info('You are: {} <{}>'.format(
          new_index.modified_by.name, new_index.modified_by.email))

    table = texttable.Texttable(max_width=0)
    table.set_deco(texttable.Texttable.HEADER)
    rows = []
    rows.append(['Action', 'Path', 'Last deployed', 'By'])
    file_rows = []
    for add in diff.adds:
      file_rows.append(cls._make_diff_row(texttable.bcolors.GREEN, 'Add', add))
    for edit in diff.edits:
      file_rows.append(cls._make_diff_row(texttable.bcolors.PURPLE, 'Edit', edit))
    for delete in diff.deletes:
      file_rows.append(cls._make_diff_row(texttable.bcolors.RED, 'Delete', delete))
    file_rows.sort(key=lambda row: row[1])
    rows += file_rows
    table.add_rows(rows)
    logging.info('\n' + table.draw() + '\n')

  @classmethod
  def create(cls, index, theirs):
    diff = messages.DiffMessage()
    diff.indexes = []
    diff.indexes.append(theirs or messages.IndexMessage())
    diff.indexes.append(index or messages.IndexMessage())

    index_paths_to_shas = {}
    their_paths_to_shas = {}

    for file_message in index.files:
      index_paths_to_shas[file_message.path] = file_message.sha
    for file_message in theirs.files:
      their_paths_to_shas[file_message.path] = file_message.sha

    for path, sha in index_paths_to_shas.iteritems():
      if path in their_paths_to_shas:
        if index_paths_to_shas[path] == their_paths_to_shas[path]:
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
        del their_paths_to_shas[path]
      else:
        file_message = messages.FileMessage()
        file_message.path = path
        diff.adds.append(file_message)

    for path, sha in their_paths_to_shas.iteritems():
      file_message = messages.FileMessage()
      file_message.path = path
      file_message.modified = theirs.modified
      file_message.modified_by = theirs.modified_by
      diff.deletes.append(file_message)

    return diff

  @classmethod
  def apply(cls, message, paths_to_content, write_func, delete_func, threaded=True):
    diff = message
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


class Index(object):

  @classmethod
  def create(cls, paths_to_contents=None):
    message = messages.IndexMessage()
    message.modified = datetime.datetime.now()
    message.files = []
    if paths_to_contents is None:
      return message
    for pod_path, contents in paths_to_contents.iteritems():
      cls.add_file(message, pod_path, contents)
    return message

  @classmethod
  def add_file(cls, message, path, contents):
    pod_path = '/' + path.lstrip('/')
    m = hashlib.sha1()
    if isinstance(contents, unicode):
      contents = contents.encode('utf-8')
    m.update(contents)
    sha = m.hexdigest()
    message.files.append(messages.FileMessage(path=pod_path, sha=sha))
    return message

  @classmethod
  def add_repo(cls, message, repo):
    config = repo.config_reader()
    message.modified_by = messages.AuthorMessage(
        name=config.get('user', 'name'),
        email=config.get('user', 'email'))
    commit = repo.head.commit
    commit_message = messages.CommitMessage()
    commit_message.sha = commit.hexsha
    commit_message.message = commit.message
    commit_message.author = messages.AuthorMessage(
        name=commit.author.name, email=commit.author.email)
    message.commit = commit_message
    return message

  @classmethod
  def to_string(cls, message):
    return protojson.encode_message(message)

  @classmethod
  def from_string(cls, content):
    return protojson.decode_message(messages.IndexMessage, content)
