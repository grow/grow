"""Renderer for performing render operations for the pod."""

import sys
import traceback
import progressbar
from grow.common import progressbar_non
from grow.common import utils

if utils.is_appengine():
    # pylint: disable=invalid-name
    pool = None
else:
    from multiprocessing import pool


class Error(Exception):
    """Base renderer error."""
    pass


class RenderError(Error):
    """Errors that occured during the rendering."""

    def __init__(self, message, exc, err_tb):
        super(RenderError, self).__init__(message)
        self.exc = exc
        self.err_tb = err_tb


class RenderErrors(Error):
    """Errors that occured during the rendering."""

    def __init__(self, message, errors):
        super(RenderErrors, self).__init__(message)
        self.errors = errors


class Renderer(object):
    """Handles the rendering and threading of the controllers."""
    POOL_SIZE = 10  # Thread pool size for rendering.

    # pylint: disable=too-many-locals
    @staticmethod
    def rendered_docs(pod, routes):
        """Generate the rendered documents for the given routes."""
        cont_generator = Renderer.controller_generator(pod, routes)

        # Preload the render_pool before attempting to use.
        _ = pod.render_pool

        def render_func(controller):
            """Render the content."""
            try:
                return controller.render()
            # pylint: disable=broad-except
            except Exception as err:
                _, _, err_tb = sys.exc_info()
                return RenderError(
                    "Error rendering {}".format(controller.serving_path),
                    err, err_tb)

        routes_len = len(routes)
        text = 'Building: %(value)d/{} (in %(time_elapsed).9s)'
        widgets = [progressbar.FormatLabel(text.format(routes_len))]
        progress = progressbar_non.create_progressbar(
            "Building pod...", widgets=widgets, max_value=routes_len)
        progress.start()

        rendered_docs = []
        if not pool:
            for controller in cont_generator:
                rendered_docs.append(render_func(controller))
                progress.update(progress.value + 1)
            progress.finish()
            return rendered_docs

        thread_pool = pool.ThreadPool(Renderer.POOL_SIZE)
        results = thread_pool.imap_unordered(render_func, cont_generator)

        render_errors = []

        for result in results:
            if isinstance(result, Exception):
                render_errors.append(result)
            else:
                rendered_docs.append(result)
            progress.update(progress.value + 1)
        thread_pool.close()
        thread_pool.join()
        progress.finish()

        if render_errors:
            for error in render_errors:
                traceback.print_tb(error.err_tb)
            text = 'There were {} errors during rendering.'
            raise RenderErrors(text.format(len(render_errors)), render_errors)

        return rendered_docs

    @staticmethod
    def controller_generator(pod, routes):
        """Generate the controllers for the given routes."""
        for path, route_info in routes.nodes:
            yield pod.router.get_render_controller(path, route_info)
