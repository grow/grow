"""Subcommand for displaying all routes of a pod."""

import collections
import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.pods import pods
from grow import storage


CFG = rc_config.RC_CONFIG.prefixed('grow.routes')


@click.command(name='routes')
@shared.pod_path_argument
@shared.reroute_option(CFG)
def inspect_routes(pod_path, use_reroute):
    """Lists routes handled by a pod."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage, use_reroute=use_reroute)
    with pod.profile.timer('grow_inspect_routes'):
        out = []
        if use_reroute:
            pod.router.use_simple()
            pod.router.add_all()
            for path, node in pod.router.routes.nodes:
                out.append(u'{}\n    > {}'.format(path, node))
        else:
            pod_routes = pod.get_routes()
            controllers_to_paths = collections.defaultdict(set)
            for route in pod_routes:
                name = str(route.endpoint)
                paths = route.endpoint.list_concrete_paths()
                controllers_to_paths[name].update(paths)
            for controller, paths in controllers_to_paths.iteritems():
                paths = sorted(paths)
                if len(paths) > 1 or True:
                    out.append(controller)
                    for path in paths:
                        out.append('  {}'.format(path))
                else:
                    out.append(paths[0])
                out.append('')
        click.echo_via_pager('\n'.join(out))
    return pod
