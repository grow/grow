"""Renderer for performing render operations for the pod."""

import traceback
import progressbar
from grow.common import progressbar_non
from grow.rendering import render_batch


class Error(Exception):
    """Base renderer error."""
    pass


class RenderErrors(Error):
    """Errors that occured during the rendering."""

    def __init__(self, message, errors):
        super(RenderErrors, self).__init__(message)
        self.errors = errors


class Renderer(object):
    """Handles the rendering and threading of the controllers."""

    @staticmethod
    def rendered_docs(pod, routes, use_threading=True):
        """Generate the rendered documents for the given routes."""
        with pod.profile.timer('renderer.Renderer.render_docs'):
            routes_len = len(routes)
            text = 'Building: %(value)d/{} (in %(time_elapsed).9s)'
            widgets = [progressbar.FormatLabel(text.format(routes_len))]
            progress = progressbar_non.create_progressbar(
                "Building pod...", widgets=widgets, max_value=routes_len)
            progress.start()

            def tick():
                """Tick the progress bar value."""
                progress.update(progress.value + 1)

            batches = render_batch.RenderBatches(
                pod.render_pool, pod.profile, tick=tick)

            for controller in Renderer.controller_generator(pod, routes):
                batches.add(controller)

            rendered_docs, render_errors = batches.render(
                use_threading=use_threading)
            progress.finish()

            if render_errors:
                for error in render_errors:
                    print error.message
                    print error.err.message
                    traceback.print_tb(error.err_tb)
                    print ''
                text = 'There were {} errors during rendering.'
                raise RenderErrors(text.format(
                    len(render_errors)), render_errors)
            return rendered_docs

    @staticmethod
    def controller_generator(pod, routes):
        """Generate the controllers for the given routes."""
        for path, route_info, _ in routes.nodes:
            yield pod.router.get_render_controller(path, route_info)
