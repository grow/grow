"""Subcommand for staging pod to remote server."""

import os
import click
from grow.commands import shared
from grow.common import bulk_errors
from grow.common import rc_config
from grow.common import utils
from grow.deployments import stats
from grow.deployments.destinations import base
from grow.deployments.destinations import webreview_destination
from grow.extensions import hooks
from grow.performance import docs_loader
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
@click.option('--file', '--pod-path', 'pod_paths',
              help='Build only pages affected by content files.', multiple=True)
@click.option('--subdomain', help='Assign a subdomain to this build.')
@click.option('--api-key',
              help='API key for authorizing staging to WebReview projects.')
@shared.locale_option(help_text='Filter build routes to specific locale.')
@shared.force_untranslated_option(CFG)
@shared.preprocess_option(CFG)
@shared.threaded_option(CFG)
@shared.work_dir_option
@shared.routes_file_option()
@click.pass_context
def stage(context, pod_path, remote, pod_paths, locale, preprocess, subdomain, api_key,
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
            repo = utils.get_git_repo(pod.root)
            pod.router.use_simple()
            is_partial = bool(pod_paths) or bool(locale)
            if pod_paths:
                pod_paths = [pod.clean_pod_path(path) for path in pod_paths]
                pod.router.add_pod_paths(pod_paths)
            elif routes_file:
                pod.router.from_data(pod.read_json(routes_file))
            else:
                pod.router.add_all()

            if locale:
                pod.router.filter('whitelist', locales=list(locale))

            if not work_dir:
                # Preload the documents used by the paths after filtering.
                docs_loader.DocsLoader.load_from_routes(pod, pod.router.routes)

            paths = pod.router.routes.paths
            stats_obj = stats.Stats(pod, paths=paths)
            content_generator = deployment.dump(
                pod, source_dir=work_dir, use_threading=threaded)
            content_generator = hooks.generator_wrapper(
                pod, 'pre_deploy', content_generator, 'stage')
            deployment.deploy(content_generator, stats=stats_obj, repo=repo,
                              confirm=False, test=False, require_translations=require_translations,
                              is_partial=is_partial)
            pod.podcache.write()
    except bulk_errors.BulkErrors as err:
        # Write the podcache files even when there are rendering errors.
        pod.podcache.write()
        bulk_errors.display_bulk_errors(err)
        raise click.Abort()
    # except base.Error as err:
    #     raise click.ClickException(str(err))
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
