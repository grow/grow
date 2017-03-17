from grow.common import utils
from grow.deployments import stats
from grow.deployments.destinations import base
from grow.deployments.destinations import webreview_destination
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--preprocess/--no-preprocess', '-p/-np', default=True,
              is_flag=True, help='Whether to run preprocessors.')
@click.option('--remote',
              help='WebReview remote address (example: '
                   ' example.com/owner/project). A remote must be specified'
                   ' either using --remote or by configuring a deployment'
                   ' named "webreview" in podspec.yaml.')
@click.option('--subdomain', help='Assign a subdomain to this build.')
@click.option('--api-key',
              help='API key for authorizing staging to WebReview projects.')
@click.pass_context
def stage(context, pod_path, remote, preprocess, subdomain, api_key):
    """Stages a build on a WebReview server."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    auth = context.parent.params.get('auth')
    try:
        pod = pods.Pod(root, storage=storage.FileStorage)
        deployment = _get_deployment(pod, remote, subdomain, api_key)
        if auth:
            deployment.login(auth)
        if preprocess:
            pod.preprocess()
        repo = utils.get_git_repo(pod.root)
        paths_to_contents = deployment.dump(pod)
        stats_obj = stats.Stats(pod, paths_to_contents=paths_to_contents)
        deployment.deploy(paths_to_contents, stats=stats_obj, repo=repo,
                          confirm=False, test=False)
    except base.Error as e:
        raise click.ClickException(str(e))
    except pods.Error as e:
        raise click.ClickException(str(e))


def _get_deployment(pod, remote, subdomain, api_key):
    if remote:
        dest_class = webreview_destination.WebReviewDestination
        return dest_class(dest_class.Config(remote=remote, name=subdomain))
    else:
        try:
            deployment = pod.get_deployment('webreview')
            if subdomain:
                deployment.config.subdomain = subdomain
            if api_key:
                deployment.webreview.api_key = api_key
            return deployment
        except ValueError:
            text = ('Must provide --remote or specify a deployment named '
                    '"webreview" in podspec.yaml.')
            raise click.ClickException(text)
