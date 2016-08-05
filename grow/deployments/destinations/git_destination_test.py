from grow.common import utils
from grow.deployments import stats
from grow.testing import testing
from nose.plugins import skip
import os
import random
import unittest


class GitDestinationTestCase(unittest.TestCase):

    def test_deploy(self):
        repo = os.getenv('GROW_TEST_REPO_URL')
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'deployments': {
                'git': {
                    'destination': 'git',
                    'repo': repo,
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
        if utils.is_appengine():
            text = 'Skipping Git destination test on GAE.'
            raise skip.SkipTest(text)
        deployment = pod.get_deployment('git')
        paths_to_contents = deployment.dump(pod)
        repo = utils.get_git_repo(pod.root)
        stats_obj = stats.Stats(pod, paths_to_contents=paths_to_contents)
        if not repo:
            text = 'Set $GROW_TEST_REPO_URL to test Git deployment.'
            raise skip.SkipTest(text)
        deployment.deploy(paths_to_contents, stats=stats_obj, repo=repo,
                          confirm=False, test=False)


if __name__ == '__main__':
    unittest.main()
