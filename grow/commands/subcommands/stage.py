"""Subcommand for staging pod to remote server."""

import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.common import utils
from grow.deployments import stats
from grow.deployments.destinations import base
from grow.deployments.destinations import webreview_destination
from grow.pods import pods
from grow.rendering import renderer
from grow import storage


CFG = rc_config.RC_CONFIG.prefixed('grow.stage')


# pylint: disable=too-many-locals
@click.command()
@shared.pod_path_argument
@click.option('--remote',
              help='WebReview remote address (example: '
                   ' example.com/owner/project). A remote must be specified'
                   ' either using --remote or by configuring a deployment'
                   ' named "webreview" in podspec.yaml.')
@click.option('--subdomain', help='Assign a subdomain to this build.')
@click.option('--api-key',
              help='API key for authorizing staging to WebReview projects.')
@shared.force_untranslated_option(CFG)
@shared.preprocess_option(CFG)
@shared.threaded_option(CFG)
@shared.work_dir_option
@shared.routes_file_option()
@click.pass_context
def stage(context, pod_path, remote, preprocess, subdomain, api_key,
          force_untranslated, threaded, work_dir, routes_file):
    """Stages a build on a WebReview server."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    auth = context.parent.params.get('auth')
    try:
        pod = pods.Pod(root, storage=storage.FileStorage)
        with pod.profile.timer('grow_stage'):
            deployment = _get_deployment(pod, remote, subdomain, api_key)
            # use the deployment's environment for preprocessing and later
            # steps.
            pod.set_env(deployment.get_env())
            # Always clear the cache when building.
            pod.podcache.reset()
            require_translations = \
                pod.podspec.localization \
                and pod.podspec.localization.get('require_translations', False)
            require_translations = require_translations \
                and not force_untranslated
            if auth:
                deployment.login(auth)
            if preprocess:
                pod.preprocess()
            content_generator = deployment.dump(
                pod, source_dir=work_dir, use_threading=threaded)
            repo = utils.get_git_repo(pod.root)
            pod.router.use_simple()
            if routes_file:
                pod.router.from_data(pod.read_json(routes_file))
            else:
                pod.router.add_all()
            paths = pod.router.routes.paths
            stats_obj = stats.Stats(pod, paths=paths)
            deployment.deploy(content_generator, stats=stats_obj, repo=repo,
                              confirm=False, test=False, require_translations=require_translations)
            pod.podcache.write()
    except renderer.RenderErrors as err:
        # Write the podcache files even when there are rendering errors.
        pod.podcache.write()
        # Ignore the build error since it outputs the errors.
        raise click.ClickException(str(err))
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
