import cStringIO
import logging
import os
from dulwich import repo
from dulwich import object_store
from dulwich import client
from dulwich import pack
from dulwich import index

THEME_REPO_URL = 'https://github.com/growthemes/{}.git'


def init(pod, theme_url):
    if '//' not in theme_url or ':' not in theme_url:
      repo_url = THEME_REPO_URL.format(theme_url)
    else:
      repo_url = theme_url
    git_client = client.HttpGitClient(repo_url)
    logging.info('Initializing with {}...'.format(repo_url))
    temp_repo = MemoryRepo()
    temp_repo.clone(git_client)
    tree = temp_repo['refs/heads/master'].tree
    try:
      local_repo = repo.Repo.init(pod.root, mkdir=True)
    except OSError as e:
      if 'File exists' in str(e):
        text = '{} already exists. Delete the directory before proceeding.'
        logging.info(text.format(pod.root))
        return
    index_file = local_repo.index_path()
    index.build_index_from_tree(local_repo.path, index_file, temp_repo.object_store, tree)
    logging.info('Pod ready to go: {}'.format(pod.root))
    git_dir = os.path.join(pod.root, '.git')
    pod.storage.delete_dir(git_dir)


class MemoryObjectStore(object_store.MemoryObjectStore):

  def add_pack(self):
    content = cStringIO.StringIO()

    def abort():
      pass

    def store():
      temp_file = cStringIO.StringIO(content.getvalue())
      pack_data = pack.PackData.from_file(temp_file, content.tell())
      for obj in pack.PackInflater.for_pack_data(pack_data):
        self.add_object(obj)

    return content, store, abort


class MemoryRepo(repo.MemoryRepo):

  def __init__(self):
    repo.BaseRepo.__init__(self, MemoryObjectStore(),
                           repo.DictRefsContainer({}))
    self._named_files = {}
    self.bare = True

  def clone(self, client):
    refs = client.fetch('', self)
    for name, ref in refs.iteritems():
      self.refs.add_if_new(name, ref)

  def get_content(self, filename, commit_id=None):
    if commit_id is None:
      commit_id = self.head()
    commit = self.get_object(commit_id)
    tree = self.get_object(commit.tree)
    blob = self.get_object(tree[filename][1])
    return blob.data
