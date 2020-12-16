import git
from grow.common import utils
from grow.deployments import messages


class Error(Exception):

    def __init__(self, message):
        super(Error, self).__init__(message)
        self.message = message


class NoGitHeadError(Error, ValueError):
    pass


def create_commit_message(repo):
    message = messages.CommitMessage()
    try:
        commit = repo.head.commit
    except ValueError:
        raise NoGitHeadError('On initial commit, no HEAD yet.')
    try:
        repo.git.diff('--quiet')
        has_unstaged_changes = False
    except git.GitCommandError:  # pragma: no cover
        has_unstaged_changes = True
    message.has_unstaged_changes = has_unstaged_changes
    message.sha = commit.hexsha
    message.message = commit.message
    try:
        message.branch = repo.head.ref.name
    except TypeError:
        # Allow operating in an environment with a detached HEAD.
        pass
    message.author = messages.AuthorMessage(
        name=commit.author.name, email=commit.author.email)
    return message
