from . import base
from .. import utils
from grow.common import utils as common_utils
from grow.pods import env
from protorpc import messages
import logging
import os
import urlparse


if common_utils.is_appengine():
    webreview = None
else:
    import webreview


class Config(messages.Message):
    env = messages.MessageField(env.EnvConfig, 1)
    project = messages.StringField(2, required=True)
    name = messages.StringField(3)
    server = messages.StringField(4, required=True)
    secure = messages.BooleanField(5, default=True)
    keep_control_dir = messages.BooleanField(6, default=False)
    remote = messages.StringField(8)
    subdomain = messages.StringField(9)
    subdomain_prefix = messages.StringField(10)


class WebReviewDestination(base.BaseDestination):
    KIND = 'webreview'
    Config = Config
    threaded = True
    batch_writes = True

    def __init__(self, *args, **kwargs):
        super(WebReviewDestination, self).__init__(*args, **kwargs)
        if webreview is None:
            raise common_utils.UnavailableError('WebReview deployments are not available in this environment.')
        if self.config.name:
            print ('WARNING: The "name" parameter for webreview deployments is '
                   'deprecated. Use "subdomain" instead, or use the "grow stage '
                   '--subdomain=<subdomain>" command.')
            self.config.subdomain = self.config.name
        if self.config.remote:
            self.config.server, self.config.project = self.config.remote.split('/', 1)
        if self.config.server.startswith('localhost:'):
            self.config.secure = False
        self._webreview = None

    def __str__(self):
        return self.config.server

    def get_env(self):
        """Returns an environment object based on the config."""
        if self.config.env:
            return env.Env(self.config.env)
        subdomain = self._get_subdomain()
        host = '{}-dot-{}'.format(subdomain, self.config.server)
        config = env.EnvConfig(name='webreview', host=host, scheme='https')
        return env.Env(config)

    @property
    def webreview(self):
        if self._webreview is None:
            api_key = os.getenv('WEBREVIEW_API_KEY')
            subdomain = self._get_subdomain()
            self._webreview = webreview.WebReview(
                project=self.config.project,
                name=subdomain,
                host=self.config.server,
                secure=self.config.secure,
                api_key=api_key)
        return self._webreview

    def _get_subdomain(self):
        if self.config.subdomain_prefix and not self.config.subdomain:
            repo = common_utils.get_git_repo(self.pod.root)
            try:
                token = repo.active_branch.name.split('/')[-1]
            except TypeError as e:
                # Permit staging from detached branches. Note this will clobber
                # other stages originating from detaching the same branch.
                if 'is a detached symbolic reference' not in str(e):
                    raise
                # Extract the sha from the error message.
                sha = str(e).split(' ')[-1].replace("'", '')
                token = '{}-d'.format(sha[:10])
            if token == 'master':
                return self.config.subdomain_prefix
            else:
                return self.config.subdomain_prefix + '-{}'.format(token)
        return self.config.subdomain

    def deploy(self, *args, **kwargs):
        repo = kwargs.get('repo')
        if repo:
            subdomain = self._get_subdomain()
            self.webreview.name = subdomain
            try:
                self.webreview.commit = utils.create_commit_message(repo)
            except ValueError:
                raise ValueError(
                    'Cannot deploy to WebReview from a Git repository without a HEAD.'
                    ' Commit first then deploy to WebReview.')
        result = super(WebReviewDestination, self).deploy(*args, **kwargs)
        if self.success:
            finalize_response = self.webreview.finalize()
            if 'fileset' in finalize_response:
                url = finalize_response['fileset']['url']
                # Append the homepage path to the staging link.
                result = urlparse.urlparse(url)
                if not result.path and self.pod and self.pod.get_home_doc():
                  home_doc = self.pod.get_home_doc()
                  url = url.rstrip('/') + home_doc.url.path
                logging.info('Staged: %s', url)
        return result

    def login(self, account='default', reauth=False):
        self.webreview.login(account, reauth=reauth)

    def prelaunch(self, dry_run=False):
        super(WebReviewDestination, self).prelaunch(dry_run=dry_run)

    def postlaunch(self, dry_run=False):
        super(WebReviewDestination, self).postlaunch(dry_run=dry_run)

    def test(self):
        # Skip the default "can write files at destination" test.
        pass

    def read_file(self, path):
        try:
            paths_to_contents, errors = self.webreview.read([path])
            if path not in paths_to_contents:
                raise IOError('{} not found.'.format(path))
            if errors:
                raise base.Error(errors)
            return paths_to_contents[path]
        except webreview.RpcError as e:
            raise base.Error(e.message)

    def write_files(self, paths_to_rendered_doc):
        try:
            paths_to_rendered_doc, errors = self.webreview.write(paths_to_rendered_doc)
            if errors:
                raise base.Error(errors)
            return paths_to_rendered_doc
        except webreview.RpcError as e:
            raise base.Error(e.message)

    def delete_file(self, paths):
        try:
            paths, errors = self.webreview.delete(paths)
            if errors:
                raise base.Error(errors)
            return paths
        except webreview.RpcError as e:
            raise base.Error(e.message)


# Support legacy "jetway" destination. Remove this in a future release.
class LegacyJetwayDestination(WebReviewDestination):
    KIND = 'jetway'
