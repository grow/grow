"""Controller for rendering pod content."""

import mimetypes
import os
import sys
from grow.pods import errors
from grow.rendering import rendered_document
from grow.templates import doc_dependency
from grow.templates import tags


class Error(Exception):
    """Base rendering pool error."""
    pass


class UnknownKindError(Exception):
    """Unknown kind of information."""
    pass


class RenderController(object):
    """Controls how the content is rendered and evaluated."""

    def __init__(self, pod, serving_path, route_info, params=None, is_threaded=False):
        self.pod = pod
        self.serving_path = serving_path
        self.route_info = route_info
        self.params = params if params is not None else {}
        self.render_timer = None
        self.use_jinja = False
        self.is_threaded = is_threaded

    @staticmethod
    def from_route_info(pod, serving_path, route_info, params=None):
        """Create the correct controller based on the route info."""
        if params is None:
            params = {}
        kind = route_info.kind
        if kind == 'doc':
            return RenderDocumentController(
                pod, serving_path, route_info, params=params)
        elif kind == 'static':
            return RenderStaticDocumentController(
                pod, serving_path, route_info, params=params)
        elif kind == 'sitemap':
            return RenderSitemapController(
                pod, serving_path, route_info, params=params)
        elif kind == 'error':
            return RenderErrorController(
                pod, serving_path, route_info, params=params)
        raise UnknownKindError('Do not have a controller for: {}'.format(kind))

    @property
    def locale(self):
        """Locale to use for rendering."""
        return None

    @property
    def mimetype(self):
        """Guess the mimetype of the content."""
        return 'text/plain'

    def get_http_headers(self):
        """Determine headers to serve for https requests."""
        headers = {}
        mimetype = self.mimetype
        if mimetype:
            headers['Content-Type'] = mimetype
        return headers

    def render(self, jinja_env):
        """Render the pod content."""
        raise NotImplementedError


class RenderDocumentController(RenderController):
    """Controller for handling rendering for documents."""

    def __init__(self, pod, serving_path, route_info, params=None, is_threaded=False):
        super(RenderDocumentController, self).__init__(
            pod, serving_path, route_info, params=params, is_threaded=is_threaded)
        self._doc = None
        self.use_jinja = True

    @property
    def doc(self):
        """Doc for the controller."""
        if not self._doc:
            pod_path = self.route_info.meta['pod_path']
            locale = self.route_info.meta.get(
                'locale', self.params.get('locale'))
            self._doc = self.pod.get_doc(pod_path, locale=locale)
        return self._doc

    @property
    def locale(self):
        """Locale to use for rendering."""
        return self.doc.locale if self.doc else None

    @property
    def mimetype(self):
        """Determine headers to serve for https requests."""
        return mimetypes.guess_type(self.doc.view)[0]

    @property
    def suffix(self):
        """Determine headers to serve for https requests."""
        _, ext = os.path.splitext(self.doc.view)
        if ext == '.html':
            return 'index.html'
        return ''

    def render(self, jinja_env=None):
        """Render the document using the render pool."""
        timer = self.pod.profile.timer(
            'RenderDocumentController.render',
            label='{} ({})'.format(self.doc.pod_path, self.doc.locale),
            meta={
                'path': self.doc.pod_path,
                'locale': str(self.doc.locale)}
        ).start_timer()
        doc = self.doc
        with jinja_env['lock']:
            template = jinja_env['env'].get_template(doc.view.lstrip('/'))
            track_dependency = doc_dependency.DocDependency(doc)
            local_tags = tags.create_builtin_tags(
                self.pod, doc, track_dependency=track_dependency)
            # NOTE: This should be done using get_template(... globals=...)
            # or passed as an argument into render but
            # it is not available included inside macros???
            # See: https://github.com/pallets/jinja/issues/688
            template.globals['g'] = local_tags

            # Track the message stats, including untranslated strings.
            if self.pod.is_enabled(self.pod.FEATURE_TRANSLATION_STATS):
                template.globals['_'] = tags.make_doc_gettext(doc)

            try:
                serving_path = doc.get_serving_path()
                if serving_path.endswith('/'):
                    serving_path = '{}{}'.format(serving_path, self.suffix)
                rendered_content = template.render({
                    'doc': doc,
                    'env': self.pod.env,
                    'podspec': self.pod.podspec,
                    '_track_dependency': track_dependency,
                }).lstrip()
                rendered_content = self.pod.extensions_controller.trigger(
                    'post_render', doc, rendered_content)
                rendered_doc = rendered_document.RenderedDocument(
                    serving_path, rendered_content)
                timer.stop_timer()
                return rendered_doc
            except Exception as err:
                text = 'Error building {}: {}'
                if self.pod:
                    self.pod.logger.exception(text.format(self, err))
                exception = errors.BuildError(text.format(self, err))
                exception.traceback = sys.exc_info()[2]
                exception.controller = self
                exception.exception = err
                raise exception


class RenderErrorController(RenderController):
    """Controller for handling rendering for errors."""

    def __init__(self, pod, serving_path, route_info, params=None, is_threaded=False):
        super(RenderErrorController, self).__init__(
            pod, serving_path, route_info, params=params, is_threaded=is_threaded)
        self.use_jinja = True

    def render(self, jinja_env=None):
        """Render the document using the render pool."""

        timer = self.pod.profile.timer(
            'RenderErrorController.render',
            label='{} ({})'.format(
                self.route_info.meta['key'], self.route_info.meta['view']),
            meta={
                'key': self.route_info.meta['key'],
                'view': self.route_info.meta['view'],
            }
        ).start_timer()

        with jinja_env['lock']:
            template = jinja_env['env'].get_template(
                self.route_info.meta['view'].lstrip('/'))
            local_tags = tags.create_builtin_tags(self.pod, doc=None)
            # NOTE: This should be done using get_template(... globals=...)
            # or passed as an argument into render but
            # it is not available included inside macros???
            # See: https://github.com/pallets/jinja/issues/688
            template.globals['g'] = local_tags

            try:
                serving_path = '/{}.html'.format(self.route_info.meta['key'])
                rendered_doc = rendered_document.RenderedDocument(
                    serving_path, template.render({
                        'doc': None,
                        'env': self.pod.env,
                        'podspec': self.pod.podspec,
                    }).lstrip())
                timer.stop_timer()
                return rendered_doc
            except Exception as err:
                text = 'Error building {}: {}'
                if self.pod:
                    self.pod.logger.exception(text.format(self, err))
                exception = errors.BuildError(text.format(self, err))
                exception.traceback = sys.exc_info()[2]
                exception.controller = self
                exception.exception = err
                raise exception


class RenderSitemapController(RenderController):
    """Controller for handling rendering for sitemaps."""
    pass


class RenderStaticDocumentController(RenderController):
    """Controller for handling rendering for static documents."""

    def __init__(self, pod, serving_path, route_info, params=None, is_threaded=False):
        super(RenderStaticDocumentController, self).__init__(
            pod, serving_path, route_info, params=params, is_threaded=is_threaded)
        self._static_doc = None

    @property
    def static_doc(self):
        """Static doc for the controller."""
        if not self._static_doc:
            if 'pod_path' in self.route_info.meta:
                pod_path = self.route_info.meta['pod_path']
            else:
                pod_path = '{}{}'.format(
                    self.route_info.meta['source_format'], self.params['*'])
            locale = self.route_info.meta.get(
                'locale', self.params.get('locale'))
            self._static_doc = self.pod.get_static(pod_path, locale=locale)
        return self._static_doc

    @property
    def mimetype(self):
        """Determine headers to serve for https requests."""
        return mimetypes.guess_type(self.serving_path)[0]

    def render(self, jinja_env=None):
        """Read the static file."""
        timer = self.pod.profile.timer(
            'RenderStaticDocumentController.render', label=self.serving_path,
            meta={'path': self.serving_path}).start_timer()
        pod_path = None
        if 'pod_path' in self.route_info.meta:
            pod_path = self.route_info.meta['pod_path']
        else:
            pod_path = self.serving_path[
                len(self.route_info.meta['path_format']):]
            pod_path = os.path.join(
                self.route_info.meta['source_format'], pod_path)

        if not self.pod.file_exists(pod_path):
            text = '{} was not found in static files.'
            raise errors.RouteNotFoundError(text.format(self.serving_path))

        rendered_content = self.pod.read_file(pod_path)
        rendered_content = self.pod.extensions_controller.trigger(
            'post_render', self.static_doc, rendered_content)
        rendered_doc = rendered_document.RenderedDocument(
            self.serving_path, rendered_content)
        timer.stop_timer()
        return rendered_doc
