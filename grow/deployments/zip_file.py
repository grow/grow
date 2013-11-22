import datetime
import logging
import os
import zipfile
from grow.deployments import base


class ZipFileDeployment(base.BaseDeployment):

  def __init__(self, out_dir, basename=None):
    self.out_dir = os.path.expanduser(out_dir)
    if basename is None:
      basename = datetime.datetime.now().strftime('%Y-%m-%d.%H%M%S') + '.zip'
    self.filename = os.path.join(self.out_dir, basename)

  def deploy(self, pod):
    logging.info('Creating zip file to: {}'.format(self.filename))

    fp = pod.storage.open(self.filename, 'w')
    zip_file = zipfile.ZipFile(fp, mode='w')

    paths_to_content = pod.dump()
    for path, content in paths_to_content.iteritems():
      if isinstance(content, unicode):
        content = content.encode('utf-8')
      zip_file.writestr(path, content)

    zip_file.close()
    fp.close()
    return self.filename

  def snapshot(self, pod):
    logging.info('Creating zip file to: {}'.format(self.filename))

    fp = pod.storage.open(self.filename, 'w')
    zip_file = zipfile.ZipFile(fp, mode='w')

    for path in pod.list_dir('/'):
      content = pod.read_file(path)
      if isinstance(content, unicode):
        content = content.encode('utf-8')
      zip_file.writestr(path, content)

    zip_file.close()
    fp.close()
    return self.filename
