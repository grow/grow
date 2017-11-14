"""Tests for the deployment utils."""

import unittest
import mock
from grow.deployments import utils


class UtilsTest(unittest.TestCase):
    """Tests for the deployment utils."""

    def _mock_author(self, **kwargs):
        author = mock.Mock()
        name = kwargs['name'] if 'name' in kwargs else 'name'
        type(author).name = mock.PropertyMock(return_value=name)
        email = kwargs['email'] if 'email' in kwargs else 'email'
        type(author).email = mock.PropertyMock(return_value=email)
        return author

    def _mock_commit(self, **kwargs):
        commit = mock.Mock()
        sha = kwargs['sha'] if 'sha' in kwargs else 'sha'
        type(commit).hexsha = mock.PropertyMock(return_value=sha)
        message = kwargs['message'] if 'message' in kwargs else 'message'
        type(commit).message = mock.PropertyMock(return_value=message)
        branch = kwargs['branch'] if 'branch' in kwargs else 'branch'
        type(commit).branch = mock.PropertyMock(return_value=branch)
        author = kwargs['author'] if 'author' in kwargs else self._mock_author(**kwargs)
        type(commit).author = mock.PropertyMock(return_value=author)
        return commit

    def _mock_head(self, **kwargs):
        head = mock.Mock()
        ref = kwargs['ref'] if 'ref' in kwargs else self._mock_ref(**kwargs)
        type(head).ref = mock.PropertyMock(return_value=ref)
        if 'commit_side_effect' in kwargs:
            type(head).commit = mock.PropertyMock(side_effect=kwargs['commit_side_effect'])
        else:
            commit = kwargs['commit'] if 'commit' in kwargs else self._mock_commit(**kwargs)
            type(head).commit = mock.PropertyMock(return_value=commit)
        return head

    def _mock_ref(self, **kwargs):
        ref = mock.Mock()
        if 'name_side_effect' in kwargs:
            type(ref).name = mock.PropertyMock(side_effect=kwargs['name_side_effect'])
        else:
            name = kwargs['name'] if 'name' in kwargs else 'name'
            type(ref).name = mock.PropertyMock(return_value=name)
        return ref

    def _mock_repo(self, **kwargs):
        repo = mock.Mock()
        head = kwargs['head'] if 'head' in kwargs else self._mock_head(**kwargs)
        type(repo).head = mock.PropertyMock(return_value=head)
        return repo

    @mock.patch('grow.common.utils.get_git')
    def test_commit_message(self, _):
        """Create normal commit message."""
        mock_repo = self._mock_repo()
        message = utils.create_commit_message(mock_repo)
        self.assertEqual(message.sha, 'sha')

    @mock.patch('grow.common.utils.get_git')
    def test_commit_message_error(self, _):
        """Fails without git head."""
        head = self._mock_head(commit_side_effect=ValueError('Bang!'))
        mock_repo = self._mock_repo(head=head)
        with self.assertRaises(utils.NoGitHeadError):
            utils.create_commit_message(mock_repo)

    @mock.patch('grow.common.utils.get_git')
    def test_commit_message_ref_error(self, _):
        """Continues without head ref."""
        ref = self._mock_ref(name_side_effect=TypeError('Bang!'))
        mock_repo = self._mock_repo(ref=ref)
        utils.create_commit_message(mock_repo)

if __name__ == '__main__':
    unittest.main()
