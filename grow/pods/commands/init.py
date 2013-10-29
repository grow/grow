import cStringIO
import logging
import os
from dulwich import repo
from dulwich import object_store
from dulwich import client
from dulwich import pack
from dulwich import index

REPO_URL = 'https://github.com/grow/grow-templates.git'


def init(pod, branch_name, repo_url=REPO_URL):
    branch_name = 'HEAD'  # TODO: fix this.
    git_client = client.HttpGitClient(repo_url)
    logging.info('Grabbing pod theme {} from {}...'.format(branch_name, repo_url))
    temp_repo = MemoryRepo()
    temp_repo.clone(git_client)
    tree = temp_repo[branch_name].tree
#    try:
    local_repo = repo.Repo.init(pod.root, mkdir=True)
#    except OSError as e:
#      if 'File exists' in str(e):
#        logging.info('{} already exists. Delete the directory before proceeding.'.format(pod.root))
#        return
    index_file = local_repo.index_path()
    index.build_index_from_tree(local_repo.path, index_file, temp_repo.object_store, tree)
    logging.info('Pod with theme {} is ready to go in: {}'.format(branch_name, pod.root))
    unnecessary_git_dir = os.path.join(pod.root, '.git')
    pod.storage.delete_dir(unnecessary_git_dir)


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
