"""Renderer for performing render operations for the pod."""

import progressbar
from grow.common import progressbar_non
from grow.common import bulk_errors
from grow.rendering import render_batch


class Renderer(object):
    """Handles the rendering and threading of the controllers."""

    @staticmethod
    def rendered_docs(pod, routes, use_threading=True, source_dir=None):
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

            if source_dir:
                # When using an input directory, load the files instead of render.
                rendered_docs, render_errors = batches.load(
                    use_threading=use_threading, source_dir=source_dir)
            else:
                # Default to rendering the documents.
                rendered_docs, render_errors = batches.render(
                    use_threading=use_threading)

            progress.finish()

            if render_errors:
                text = 'There were {} errors during rendering.'
                raise bulk_errors.BulkErrors(text.format(
                    len(render_errors)), render_errors)
            return rendered_docs

    @staticmethod
    def controller_generator(pod, routes):
        """Generate the controllers for the given routes."""
        for path, route_info, _ in routes.nodes:
            yield pod.router.get_render_controller(path, route_info)
