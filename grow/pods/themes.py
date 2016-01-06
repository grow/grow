import cStringIO
import errno
import logging
import os
import shutil
import tempfile
from dulwich import repo
from dulwich import object_store
from dulwich import client
from dulwich import pack
from dulwich import index

THEME_REPO_URL = 'https://github.com/growthemes/{}.git'


def init(pod, theme_url, force=False):
    if '//' not in theme_url or ':' not in theme_url:
        repo_url = THEME_REPO_URL.format(theme_url)
    else:
        repo_url = theme_url
    git_client = client.HttpGitClient(repo_url)
    logging.info('Initializing with {}...'.format(repo_url))
    temp_repo = MemoryRepo()
    temp_repo.clone(git_client)
    tree = temp_repo['refs/heads/master'].tree

    # Build the tree into a temp directory.
    temp_root = tempfile.mkdtemp()
    local_repo = repo.Repo.init(temp_root)
    index_file = local_repo.index_path()
    index.build_index_from_tree(local_repo.path, index_file, temp_repo.object_store, tree)
    shutil.rmtree(os.path.join(temp_root, '.git'))

    # Automatically enable "force" for empty directories.
    if pod.list_dir('/') == []:
        force = True

    try:
        _copy_files_to_pod(temp_root, pod, force=force)
    except OSError as e:
        if 'File exists' in str(e):
            text = ('{} already exists and is not empty. Delete the directory before'
                    ' proceeding or use --force.')
            logging.info(text.format(pod.root))
            return
    logging.info('Pod ready to go: {}'.format(pod.root))


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


def _copy_files_to_pod(temp_root, pod, force=False):
    """Copies all files from a temp directory into the pod root."""
    if not os.path.exists(pod.root):
        shutil.copytree(temp_root, pod.root)
        return

    temp_names = os.listdir(temp_root)
    pod_names = os.listdir(pod.root)

    for name in temp_names:
        srcname = os.path.join(temp_root, name)
        dstname = os.path.join(pod.root, name)

        if name in pod_names:
            if force:
                if os.path.isdir(dstname):
                    shutil.rmtree(dstname)
                else:
                    pod.delete_file(name)
            else:
                raise OSError(errno.EEXIST, 'File exists', name)

        if os.path.isdir(srcname):
            shutil.copytree(srcname, dstname)
        else:
            shutil.copy(srcname, dstname)
