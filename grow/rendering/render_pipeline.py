"""Rendering pipeline for controlling the flow of rendering."""

from grow.common import logger as grow_logger
from grow.performance import profile
from grow.routing import router as grow_router


class RenderPipeline(grow_logger.Logger, profile.Profiler):
    """Control the rendering pipeline for content."""

    def __init__(self, pod, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pod = pod
        self.router = grow_router.Router(
            logger=self.logger, profiler=self.profiler)

    def render(self, destination):
        print('Root: {}'.format(self.pod.root_path))
        print('destination: {}'.format(destination))
