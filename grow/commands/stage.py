from grow.common import utils
from grow.deployments import stats
from grow.deployments.destinations import base
from grow.deployments.destinations import webreview_destination
from grow.pods import pods
from grow.pods import storage
import click
import os


# pylint: disable=too-many-locals
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
@click.option('--force-untranslated', 'force_untranslated', default=False, is_flag=True,
              help='Whether to force untranslated strings to be uploaded.')
@click.pass_context
def stage(context, pod_path, remote, preprocess, subdomain, api_key, force_untranslated):
    """Stages a build on a WebReview server."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    auth = context.parent.params.get('auth')
    try:
        pod = pods.Pod(root, storage=storage.FileStorage)
        with pod.profile.timer('grow_stage'):
            deployment = _get_deployment(pod, remote, subdomain, api_key)
            # use the deployment's environment for preprocessing and later
            # steps.
            pod.set_env(deployment.config.env)
            require_translations = pod.podspec.localization.get(
                'require_translations', False)
            require_translations = require_translations and not force_untranslated
            if auth:
                deployment.login(auth)
            if preprocess:
                pod.preprocess()
            content_generator = deployment.dump(pod)
            repo = utils.get_git_repo(pod.root)
            paths, _ = pod.determine_paths_to_build()
            stats_obj = stats.Stats(pod, paths=paths)
            deployment.deploy(content_generator, stats=stats_obj, repo=repo,
                              confirm=False, test=False, require_translations=require_translations)
    except base.Error as err:
        raise click.ClickException(str(err))
    except pods.Error as err:
        raise click.ClickException(str(err))
    return pod


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
