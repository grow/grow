import hashlib
import logging
import threading
import yaml
from grow.common import utils


class Error(Exception):
  pass


class CorruptIndexError(Error):
  pass


class Diff(object):

  def __init__(self, adds, edits, deletes, nochanges):
    self.adds = adds
    self.edits = edits
    self.deletes = deletes
    self.nochanges = nochanges

  def __nonzero__(self):
    return not (
        self.nochanges
        and not self.adds
        and not self.edits
        and not self.deletes)

  def __eq__(self, other):
    return (
        self.adds == other.adds
        and self.edits == other.edits
        and self.deletes == other.deletes
        and self.nochanges == other.nochanges)

  def log_pretty(self):
    logging.info(utils.colorize('\n{green}Adding files: (%s){/green}' % len(self.adds)))
    [logging.info('  {}'.format(add)) for add in self.adds]
    logging.info(utils.colorize('{yellow}Editing files: (%s){/yellow}'% len(self.edits)))
    [logging.info('  {}'.format(edit)) for edit in self.edits]
    logging.info(utils.colorize('{red}Deleting files: (%s){/red}' % len(self.deletes)))
    [logging.info('  {}'.format(delete)) for delete in self.deletes]
    logging.info(utils.colorize('{white}Unchanged files: (%s){/red}\n' % len(self.nochanges)))


class Index(object):
  BASENAME = '.growindex'

  def __init__(self, paths_to_shas=None):
    if paths_to_shas is None:
      paths_to_shas = {}
    self.paths_to_shas = paths_to_shas

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

  def diff(self, theirs):
    """Shows a diff of what will happen after applying yours to theirs."""
    diff = Diff(adds=[], edits=[], deletes=[], nochanges=[])

    for path, sha in self.iteritems():
      if path in theirs:
        if self[path] == theirs[path]:
          diff.nochanges.append(path)
        else:
          diff.edits.append(path)
        del theirs[path]
      else:
        diff.adds.append(path)

    for path, sha in theirs.iteritems():
      diff.deletes.append(path)

    return diff

  def to_yaml(self):
    return yaml.dump(self.paths_to_shas, default_flow_style=False)

  @classmethod
  def from_yaml(cls, yaml_string):
    try:
      return cls(yaml.load(yaml_string))
    except yaml.scanner.ScannerError as e:
      raise CorruptIndexError(str(e))

  @classmethod
  def apply_diffs(cls, diffs, paths_to_content, write_func, delete_func):
    # TODO(jeremydw): Thread pool.
    threads = []
    for path in diffs.adds:
      logging.info('Writing new file: {}'.format(path))
      content = paths_to_content[path]
      thread = threading.Thread(target=write_func, args=(path, content))
      threads.append(thread)
      thread.start()
    for path in diffs.edits:
      logging.info('Writing changed file: {}'.format(path))
      content = paths_to_content[path]
      thread = threading.Thread(target=write_func, args=(path, content))
      threads.append(thread)
      thread.start()
    for path in diffs.deletes:
      logging.info('Deleting file: {}'.format(path))
      thread = threading.Thread(target=delete_func, args=(path,))
      threads.append(thread)
      thread.start()
    # Unchanged files are quiet.
    # for path in diffs.nochanges:
    #  logging.info('Skipping unchanged file: {}'.format(path))
    for thread in threads:
      thread.join()
