"""Renderer for performing render operations for the pod."""

import sys
from multiprocessing.dummy import Pool as ThreadPool
from grow.pods import errors


class Error(Exception):
    """Base renderer error."""

    def __init__(self, message):
        super(Error, self).__init__(message)
        self.message = message


class RenderError(Error):
    """Errors that occured during the rendering."""

    def __init__(self, message, err, err_tb):
        super(RenderError, self).__init__(message)
        self.err = err
        self.err_tb = err_tb


class RenderNotStartedError(Error):
    """Rendering was not started."""
    pass


def load_func(batch, source_dir, tick=None):
    """Render the controller."""
    result = LoadBatchResult()
    for item in batch:
        controller = item['controller']
        try:
            result.loaded_docs.append(controller.load(source_dir))
        except errors.BuildError as err:
            result.load_errors.append(RenderError(
                "Error loading {}".format(controller.serving_path),
                err, err.traceback))
        except Exception as err:  # pylint: disable=broad-except
            _, _, err_tb = sys.exc_info()
            result.load_errors.append(RenderError(
                "Error loading {}".format(controller.serving_path),
                err, err_tb))
        finally:
            if tick:
                tick()
    return result


def render_func(batch, tick=None):
    """Render the controller."""
    result = RenderBatchResult()
    for item in batch:
        controller = item['controller']
        try:
            result.rendered_docs.append(controller.render(
                jinja_env=item['jinja_env']))
        except errors.BuildError as err:
            result.render_errors.append(RenderError(
                "Error rendering {}".format(controller.serving_path),
                err, err.traceback))
        except Exception as err:  # pylint: disable=broad-except
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
        for _, batch in self._batches.items():
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

    def load(self, source_dir, use_threading=True):
        """Load all of the batches."""
        load_errors = []
        load_docs = []

        # Disable threaded rendering until it can be fixed.
        use_threading = False

        if not ThreadPool or not use_threading:
            for _, batch in self._batches.items():
                batch_docs, batch_errors = batch.load_sync(source_dir)
                load_errors = load_errors + batch_errors
                load_docs = load_docs + batch_docs
        else:
            for _, batch in self._batches.items():
                batch.load_start(source_dir)
            for _, batch in self._batches.items():
                batch_docs, batch_errors = batch.load_finish()
                load_errors = load_errors + batch_errors
                load_docs = load_docs + batch_docs

        return load_docs, load_errors

    def render(self, use_threading=True):
        """Render all of the batches."""
        render_errors = []
        rendered_docs = []

        # Disable threaded rendering until it can be fixed.
        use_threading = False

        if not ThreadPool or not use_threading:
            for _, batch in self._batches.items():
                batch_docs, batch_errors = batch.render_sync()
                render_errors = render_errors + batch_errors
                rendered_docs = rendered_docs + batch_docs
        else:
            for _, batch in self._batches.items():
                batch.render_start()
            for _, batch in self._batches.items():
                batch_docs, batch_errors = batch.render_finish()
                render_errors = render_errors + batch_errors
                rendered_docs = rendered_docs + batch_docs

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
        self._is_loading = False
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

    def load_start(self, source_dir):
        """Start the batches loading."""
        self._thread_pool = ThreadPool(len(self.batches))
        self._results = self._thread_pool.imap_unordered(
            load_func, self.batches, source_dir)
        self._is_loading = True

    def load_finish(self):
        """Finish in progress batches loading."""
        if not self._is_loading:
            raise RenderNotStartedError('Rendering was never started')

        load_errors = []
        loaded_docs = []

        for batch_result in self._results:
            load_errors = load_errors + batch_result.load_errors
            loaded_docs = loaded_docs + batch_result.loaded_docs
            if self.tick:
                for _ in batch_result.load_errors:
                    self.tick()
                for _ in batch_result.loaded_docs:
                    self.tick()
            for result in batch_result.loaded_docs:
                self.profile.add_timer(result.load_timer)

        self._thread_pool.close()
        self._thread_pool.join()
        self._is_loading = False

        return loaded_docs, load_errors

    def load_sync(self, source_dir):
        """Syncronous loading for non-threaded loading."""
        load_errors = []
        loaded_docs = []

        for batch in self.batches:
            batch_result = load_func(batch, source_dir, tick=self.tick)
            load_errors = load_errors + batch_result.load_errors
            loaded_docs = loaded_docs + batch_result.loaded_docs

        return loaded_docs, load_errors

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


class LoadBatchResult(object):
    """Results from a batched loading."""

    def __init__(self):
        self.load_errors = []
        self.loaded_docs = []


class RenderBatchResult(object):
    """Results from a batched rendering."""

    def __init__(self):
        self.render_errors = []
        self.rendered_docs = []
