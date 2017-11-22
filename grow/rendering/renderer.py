"""Renderer for performing render operations for the pod."""

import sys
import traceback
import progressbar
from grow.common import progressbar_non
from grow.common import utils

if utils.is_appengine():
    # pylint: disable=invalid-name
    ThreadPool = None  # pragma: no cover
else:
    from multiprocessing.dummy import Pool as ThreadPool  # pylint: disable=unused-import


class Error(Exception):
    """Base renderer error."""
    pass


class RenderError(Error):
    """Errors that occured during the rendering."""

    def __init__(self, message, err, err_tb):
        super(RenderError, self).__init__(message)
        self.err = err
        self.err_tb = err_tb


class RenderErrors(Error):
    """Errors that occured during the rendering."""

    def __init__(self, message, errors):
        super(RenderErrors, self).__init__(message)
        self.errors = errors


class Renderer(object):
    """Handles the rendering and threading of the controllers."""
    POOL_SIZE = 20  # Thread pool size for rendering.

    @staticmethod
    def _handle_render_errors(render_errors):
        if render_errors:
            for error in render_errors:
                print error.message
                print error.err.message
                traceback.print_tb(error.err_tb)
                print ''
            text = 'There were {} errors during rendering.'
            raise RenderErrors(text.format(
                len(render_errors)), render_errors)

    # pylint: disable=too-many-locals
    @staticmethod
    def rendered_docs(pod, routes):
        """Generate the rendered documents for the given routes."""
        cont_generator = Renderer.controller_generator(pod, routes)

        # Turn off the pooling until it becomes faster than not pooling.
        # pylint: disable=redefined-outer-name, invalid-name
        ThreadPool = None

        with pod.profile.timer('renderer.Renderer.render_docs'):
            # Preload the render_pool before attempting to use.
            _ = pod.render_pool
            render_errors = []

            def render_func(args):
                """Render the content."""
                controller = args['controller']
                try:
                    return controller.render(jinja_env=args['jinja_env'])
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
            if not ThreadPool:
                for controller in cont_generator:
                    jinja_env = pod.render_pool.get_jinja_env(
                        controller.locale) if controller.use_jinja else None
                    result = render_func({
                        'controller': controller,
                        'jinja_env': jinja_env,
                    })
                    if isinstance(result, Exception):
                        render_errors.append(result)
                    else:
                        rendered_docs.append(result)
                    progress.update(progress.value + 1)
                progress.finish()
                Renderer._handle_render_errors(render_errors)
                return rendered_docs

            pod.render_pool.pool_size = Renderer.POOL_SIZE

            # pylint: disable=not-callable
            thread_pool = ThreadPool(Renderer.POOL_SIZE)
            threaded_args = []
            for controller in cont_generator:
                jinja_env = pod.render_pool.get_jinja_env(
                    controller.doc.locale) if controller.use_jinja else None
                threaded_args.append({
                    'controller': controller,
                    'jinja_env': jinja_env,
                })
            results = thread_pool.imap_unordered(render_func, threaded_args)

            for result in results:
                if isinstance(result, Exception):
                    render_errors.append(result)
                else:
                    pod.profile.add_timer(result.render_timer)
                progress.update(progress.value + 1)
            thread_pool.close()
            thread_pool.join()
            progress.finish()

            Renderer._handle_render_errors(render_errors)
            return rendered_docs

    @staticmethod
    def controller_generator(pod, routes):
        """Generate the controllers for the given routes."""
        for path, route_info in routes.nodes:
            yield pod.router.get_render_controller(path, route_info)
