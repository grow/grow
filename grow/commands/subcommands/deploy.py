
"""Subcommand for deploying pod."""

import os
import click
from grow.commands import shared
from grow.common import bulk_errors
from grow.common import rc_config
from grow.common import utils
from grow.deployments import stats
from grow.deployments.destinations import base
from grow.extensions import hooks
from grow.performance import docs_loader
from grow.pods import pods
from grow.rendering import renderer
from grow import storage


CFG = rc_config.RC_CONFIG.prefixed('grow.deploy')


@click.command()
@click.argument('deployment_name', default='default')
@shared.pod_path_argument
@click.option('--confirm/--noconfirm', '-c/-f', default=CFG.get('force', True), is_flag=True,
              help='Whether to confirm prior to deployment.')
@click.option('--test/--notest', default=CFG.get('test', True), is_flag=True,
              help='Whether to run deployment tests.')
@click.option('--test_only', default=False, is_flag=True,
              help='Only run the deployment tests.')
@click.option('--auth',
              help='(deprecated) --auth must now be specified'
                   ' before deploy. Usage: grow --auth=user@example.com deploy')
@shared.force_untranslated_option(CFG)
@shared.preprocess_option(CFG)
@shared.threaded_option(CFG)
@shared.shards_option
@shared.shard_option
@shared.work_dir_option
@shared.routes_file_option()
@click.pass_context
def deploy(context, deployment_name, pod_path, preprocess, confirm, test,
           test_only, auth, force_untranslated, threaded, shards, shard,
           work_dir, routes_file):
    """Deploys a pod to a destination."""
    if auth:
        text = ('--auth must now be specified before deploy. Usage:'
                ' grow --auth=user@example.com deploy')
        raise click.ClickException(text)
    auth = context.parent.params.get('auth')
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    try:
        pod = pods.Pod(root, storage=storage.FileStorage)
        with pod.profile.timer('grow_deploy'):
            # Always clear the cache when building.
            pod.podcache.reset()
            deployment = pod.get_deployment(deployment_name)
            # use the deployment's environment for preprocessing and later
            # steps.
            if deployment.config.env:
                pod.set_env(deployment.config.env)
            require_translations = pod.podspec.localization.get(
                'require_translations', False)
            require_translations = require_translations and not force_untranslated
            if auth:
                deployment.login(auth)
            if preprocess:
                pod.preprocess()
            if test_only:
                deployment.test()
                return
            repo = utils.get_git_repo(pod.root)
            pod.router.use_simple()
            if routes_file:
                pod.router.from_data(pod.read_json(routes_file))
            else:
                pod.router.add_all()
            is_partial = False
            # Filter routes based on deployment config.
            for build_filter in deployment.filters:
                is_partial = True
                pod.router.filter(
                    build_filter.type, collection_paths=build_filter.collections,
                    paths=build_filter.paths, locales=build_filter.locales)

            # Shard the routes when using sharding.
            if shards and shard:
                is_partial = True
                pod.router.shard(shards, shard)

            if not work_dir:
                # Preload the documents used by the paths after filtering.
                docs_loader.DocsLoader.load_from_routes(pod, pod.router.routes)

            paths = pod.router.routes.paths
            stats_obj = stats.Stats(pod, paths=paths)
            content_generator = deployment.dump(
                pod, source_dir=work_dir, use_threading=threaded)
            content_generator = hooks.generator_wrapper(
                pod, 'pre_deploy', content_generator, 'deploy')
            deployment.deploy(
                content_generator, stats=stats_obj, repo=repo, confirm=confirm,
                test=test, require_translations=require_translations,
                is_partial=is_partial)
            pod.podcache.write()
    except bulk_errors.BulkErrors as err:
        # Write the podcache files even when there are rendering errors.
        pod.podcache.write()
        bulk_errors.display_bulk_errors(err)
        raise click.Abort()
    except base.Error as err:
        raise click.ClickException(str(err))
    except pods.Error as err:
        raise click.ClickException(str(err))
    return pod
