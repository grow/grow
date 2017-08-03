from grow.common import utils
from grow.deployments import stats
from grow.deployments.destinations import base
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('deployment_name', required=False, default='default')
@click.argument('pod_path', default='.')
@click.option('--preprocess/--no-preprocess', '-p/-np', default=True,
              is_flag=True, help='Whether to run preprocessors.')
@click.option('--confirm/--noconfirm', '-c/-f', default=True, is_flag=True,
              help='Whether to confirm prior to deployment.')
@click.option('--test/--notest', default=True, is_flag=True,
              help='Whether to run deployment tests.')
@click.option('--test_only', default=False, is_flag=True,
              help='Only run the deployment tests.')
@click.option('--auth',
              help='(deprecated) --auth must now be specified'
                   ' before deploy. Usage: grow --auth=user@example.com deploy')
@click.option('--force-untranslated', 'force_untranslated', default=False, is_flag=True,
              help='Whether to force untranslated strings to be uploaded.')
@click.pass_context
def deploy(context, deployment_name, pod_path, preprocess, confirm, test,
           test_only, auth, force_untranslated):
    """Deploys a pod to a destination."""
    if auth:
        text = ('--auth must now be specified before deploy. Usage:'
                ' grow --auth=user@example.com deploy')
        raise click.ClickException(text)
    auth = context.parent.params.get('auth')
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    try:
        pod = pods.Pod(root, storage=storage.FileStorage)
        deployment = pod.get_deployment(deployment_name)
        prevent_untranslated = deployment.prevent_untranslated and not force_untranslated
        # use the deployment's environment for preprocessing and later steps.
        pod.set_env(deployment.config.env)
        if prevent_untranslated:
            pod.enable(pod.FEATURE_TRANSLATION_STATS)
        if auth:
            deployment.login(auth)
        if preprocess:
            pod.preprocess()
        if test_only:
            deployment.test()
            return
        paths_to_contents = deployment.dump(pod)
        if prevent_untranslated and pod.translation_stats.untranslated:
            pod.translation_stats.pretty_print()
            raise pods.Error('Aborted deploy due to untranslated strings. '
                             'Use the --force-untranslated flag to force deployment.')
        repo = utils.get_git_repo(pod.root)
        stats_obj = stats.Stats(pod, paths_to_contents=paths_to_contents)
        deployment.deploy(paths_to_contents, stats=stats_obj, repo=repo,
                          confirm=confirm, test=test)
    except base.Error as e:
        raise click.ClickException(str(e))
    except pods.Error as e:
        raise click.ClickException(str(e))
