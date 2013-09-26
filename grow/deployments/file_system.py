import logging
import os
from grow.deployments import base
from grow.pods import index


class FileSystemDeployment(base.BaseDeployment):

  def __init__(self, out_dir):
    self.out_dir = out_dir

  def deploy(self, pod):
    logging.info('Deploying to: {}'.format(self.out_dir))
    try:
      path = os.path.join(self.out_dir, index.Index.BASENAME)
      yaml_string = pod.storage.read(path)
      current_index = index.Index.from_yaml(yaml_string)
    except IOError, e:
      if e.errno != 2:
        raise
      logging.info('No index found, assuming deploying new pod.')
      current_index = index.Index()

    paths_to_content = pod.dump()
    canary_index = index.Index()
    canary_index.update(paths_to_content)
    index_path = os.path.join(self.out_dir, index.Index.BASENAME)

    diffs = canary_index.diff(current_index)
    for path in diffs.adds:
      logging.info('Writing new file: {}'.format(path))
      self._write_file(pod, path, paths_to_content[path])
    for path in diffs.edits:
      logging.info('Writing changed file: {}'.format(path))
      self._write_file(pod, path, paths_to_content[path])
    for path in diffs.deletes:
      logging.info('Deleting file: {}'.format(path))
      self._delete_file(pod, path)
    for path in diffs.nochanges:
      logging.info('Skipping unchanged file: {}'.format(path))

    pod.storage.write(index_path, canary_index.to_yaml())
    logging.info('Wrote index: {}'.format(index_path))

  def _delete_file(self, pod, path):
    out_path = os.path.join(self.out_dir, path.lstrip('/'))
    pod.storage.delete(out_path)

  def _write_file(self, pod, path, content):
    out_path = os.path.join(self.out_dir, path.lstrip('/'))
    if isinstance(content, unicode):
      content = content.encode('utf-8')
    pod.storage.write(out_path, content)
