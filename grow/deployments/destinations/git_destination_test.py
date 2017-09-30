from grow.common import utils
from grow.deployments import stats
from grow.testing import testing
from nose.plugins import skip
import os
import random
import tempfile
import unittest


class GitDestinationTestCase(unittest.TestCase):

    def _test_deploy(self, repo_url):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'deployments': {
                'git': {
                    'destination': 'git',
                    'repo': repo_url,
                    'branch': 'gh-pages',
                },
            },
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {})
        pod.write_yaml('/content/pages/page.yaml', {
            '$path': '/{base}/',
            '$view': '/views/base.html',
        })
        pod.write_file('/views/base.html', str(random.randint(0, 999)))
        deployment = pod.get_deployment('git')
        paths = []
        for rendered_doc in deployment.dump(pod):
            paths.append(rendered_doc.path)
        repo = utils.get_git_repo(pod.root)
        stats_obj = stats.Stats(pod, paths=paths)
        deployment.deploy(deployment.dump(pod), stats=stats_obj, repo=repo,
                          confirm=False, test=False)

    def test_deploy_local(self):
        if utils.is_appengine():
            text = 'Skipping Git destination test on GAE.'
            raise skip.SkipTest(text)
        import git
        path = tempfile.mkdtemp()
        git.Repo.init(path)
        self._test_deploy(path)

    def test_deploy_online(self):
        online_url = os.getenv('GROW_TEST_REPO_URL')
        if not online_url:
            text = 'Set $GROW_TEST_REPO_URL to test online Git deployment.'
            raise skip.SkipTest(text)
        self._test_deploy(online_url)


if __name__ == '__main__':
    unittest.main()
