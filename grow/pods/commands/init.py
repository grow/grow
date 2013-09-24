import cStringIO
from dulwich import repo
from dulwich import object_store
from dulwich import client
from dulwich import pack
from dulwich import index

REPO_URL = 'https://github.com/grow/grow-templates.git'


def init(pod, branch_name, repo_url=REPO_URL):
    git_client = client.HttpGitClient(repo_url)
    temp_repo = MemoryRepo()
    temp_repo.clone(git_client)
    branch_name = 'HEAD'
    tree = temp_repo[branch_name].tree
    try:
      local_repo = repo.Repo.init(pod.root, mkdir=True)
    except OSError as e:
      if 'File exists' in str(e):
        print '{} already exists. Delete the directory before proceeding.'.format(pod.root)
        return
    index_file = local_repo.index_path()
    index.build_index_from_tree(local_repo.path, index_file,
                                temp_repo.object_store, tree)
    print 'Template {} is ready to go in {}.'.format(branch_name, pod.root)
    print 'To start Grow, use: grow run {}'.format(pod.root)


class MemoryObjectStore(object_store.MemoryObjectStore):

  def add_pack(self):
    content = cStringIO.StringIO()

    def store():
      temp_file = cStringIO.StringIO(content.getvalue())
      pack_data = pack.PackData.from_file(temp_file, content.tell())
      for obj in pack.PackInflater.for_pack_data(pack_data):
        self.add_object(obj)

    return content, store


class MemoryRepo(repo.MemoryRepo):

  def __init__(self):
    repo.BaseRepo.__init__(self, MemoryObjectStore(), repo.DictRefsContainer({}))
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
