"""Renderer for performing render operations for the pod."""

import sys
from grow.common import utils

if utils.is_appengine():
    # pylint: disable=invalid-name
    ThreadPool = None  # pragma: no cover
else:
    from multiprocessing.dummy import Pool as ThreadPool


class Error(Exception):
    """Base renderer error."""
    pass


class RenderError(Error):
    """Errors that occured during the rendering."""

    def __init__(self, message, err, err_tb):
        super(RenderError, self).__init__(message)
        self.err = err
        self.err_tb = err_tb


class RenderNotStartedError(Error):
    """Rendering was not started."""
    pass


def render_func(batch, tick=None):
    """Render the controller."""
    result = RenderBatchResult()
    for item in batch:
        controller = item['controller']
        try:
            result.rendered_docs.append(controller.render(
                jinja_env=item['jinja_env']))
        # pylint: disable=broad-except
        except Exception as err:
            _, _, err_tb = sys.exc_info()
            result.render_errors.append(RenderError(
                "Error rendering {}".format(controller.serving_path),
                err, err_tb))
        finally:
            if tick:
                tick()
    return result


class RenderBatches(object):
    """Handles the batching of rendering."""

    def __init__(self, render_pool, profile, tick=None, batch_size=None):
        self.batch_size = batch_size
        self.profile = profile
        self.render_pool = render_pool
        self.tick = tick
        self._batches = {}

    def __len__(self):
        count = 0
        for _, batch in self._batches.iteritems():
            count = count + len(batch)
        return count

    def _get_batch(self, locale):
        if locale not in self._batches:
            self._batches[locale] = RenderLocaleBatch(
                self.render_pool.get_jinja_env(locale), self.profile, tick=self.tick,
                batch_size=self.batch_size)
        return self._batches[locale]

    def add(self, controller, *args, **kwargs):
        """Add an item to be rendered to the batch."""
        batch = self._get_batch(controller.locale)
        batch.add(controller, *args, **kwargs)

    def render(self, use_threading=True):
        """Render all of the batches."""
        render_errors = []
        rendered_docs = []

        # Disable threaded rendering until it can be fixed.
        use_threading = False

        if not ThreadPool or not use_threading:
            for _, batch in self._batches.iteritems():
                docs, errors = batch.render_sync()
                render_errors = render_errors + errors
                rendered_docs = rendered_docs + docs
        else:
            for _, batch in self._batches.iteritems():
                batch.render_start()
            for _, batch in self._batches.iteritems():
                docs, errors = batch.render_finish()
                render_errors = render_errors + errors
                rendered_docs = rendered_docs + docs

        return rendered_docs, render_errors


class RenderLocaleBatch(object):
    """Handles the rendering and threading of the controllers."""

    BATCH_DEFAULT_SIZE = 300  # Default number of documents in a batch.

    def __init__(self, jinja_env, profile, tick=None, batch_size=None):
        self.batch_size = batch_size or self.BATCH_DEFAULT_SIZE
        self.jinja_env = jinja_env
        self.profile = profile
        self.tick = tick
        self.batches = [[]]
        self._is_rendering = False
        self._results = None
        self._thread_pool = None

    def __len__(self):
        count = 0
        for batch in self.batches:
            count = count + len(batch)
        return count

    def _get_batch(self):
        # Ensure that batch is not over the max size.
        batch = self.batches[len(self.batches) - 1]
        if len(batch) >= self.batch_size:
            self.batches.append([])
            batch = self.batches[len(self.batches) - 1]
        return batch

    def add(self, controller, *args, **kwargs):
        """Add an item to be rendered to the batch."""
        batch = self._get_batch()

        batch.append({
            'controller': controller,
            'jinja_env': self.jinja_env,
            'args': args,
            'kwargs': kwargs,
        })

    def render_start(self):
        """Start the batches rendering."""
        self._thread_pool = ThreadPool(len(self.batches))
        self._results = self._thread_pool.imap_unordered(
            render_func, self.batches)
        self._is_rendering = True

    def render_finish(self):
        """Finish in progress batches rendering."""
        if not self._is_rendering:
            raise RenderNotStartedError('Rendering was never started')

        render_errors = []
        rendered_docs = []

        for batch_result in self._results:
            render_errors = render_errors + batch_result.render_errors
            rendered_docs = rendered_docs + batch_result.rendered_docs
            if self.tick:
                for _ in batch_result.render_errors:
                    self.tick()
                for _ in batch_result.rendered_docs:
                    self.tick()
            for result in batch_result.rendered_docs:
                self.profile.add_timer(result.render_timer)

        self._thread_pool.close()
        self._thread_pool.join()
        self._is_rendering = False

        return rendered_docs, render_errors

    def render_sync(self):
        """Syncronous rendering for non-threaded rendering."""
        render_errors = []
        rendered_docs = []

        for batch in self.batches:
            batch_result = render_func(batch, tick=self.tick)
            render_errors = render_errors + batch_result.render_errors
            rendered_docs = rendered_docs + batch_result.rendered_docs

        return rendered_docs, render_errors


class RenderBatchResult(object):
    """Results from a batched rendering."""

    def __init__(self):
        self.render_errors = []
        self.rendered_docs = []
