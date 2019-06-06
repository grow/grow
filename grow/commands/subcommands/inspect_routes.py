"""Subcommand for displaying all routes of a pod."""

import json
import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.pods import pods
from grow import storage


CFG = rc_config.RC_CONFIG.prefixed('grow.routes')


@click.command(name='routes')
@shared.routes_file_option('Export route information to a json file.')
@shared.pod_path_argument
def inspect_routes(pod_path, routes_file):
    """Lists routes handled by a pod."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    with pod.profile.timer('grow_inspect_routes'):
        out = []
        pod.router.use_simple()
        pod.router.add_all()

        if routes_file:
            # print pod.router.routes.export()
            pod.write_file(
                routes_file,
                json.dumps(
                    pod.router.routes.export(), sort_keys=True, indent=2,
                    separators=(',', ': ')))
            print 'Exported routes to file: {}'.format(routes_file)
            return pod

        for path, node, _ in pod.router.routes.nodes:
            out.append(u'{} [{}]\n    {}\n'.format(path, node.kind, node.meta))
        click.echo_via_pager('\n'.join(out))
    return pod
