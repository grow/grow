"""Controller for rendering pod content."""

import datetime
import mimetypes
import os
import sys
import time
from grow.common import utils
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


class IgnoredPathError(Exception):
    """Document is being served at an ignored path."""
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

    def validate_path(self, *path_filters):
        """Validate that the path is valid against all filters."""
        # Default test against the pod filter for deployment specific filtering.
        path_filters = list(path_filters) or [self.pod.path_filter]
        for path_filter in path_filters:
            if not path_filter.is_valid(self.serving_path):
                text = '{} is an ignored path.'
                raise errors.RouteNotFoundError(text.format(self.serving_path))


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

        # Validate the path with the config filters.
        self.validate_path()

        doc = self.doc
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

            content = self.pod.extensions_controller.trigger('pre_render', doc, doc.body)
            if content:
                doc.format.update(content=content.encode('utf-8'))

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

        # Validate the path with the config filters.
        self.validate_path()

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

    @property
    def mimetype(self):
        """Determine headers to serve for https requests."""
        return mimetypes.guess_type(self.serving_path)[0]

    def render(self, jinja_env=None):
        """Render the document using the render pool."""

        timer = self.pod.profile.timer(
            'RenderSitemapController.render',
            label='{}'.format(self.serving_path),
            meta=self.route_info.meta,
        ).start_timer()

        # Validate the path with the config filters.
        self.validate_path()

        # Need a custom root for rendering sitemap.
        root = os.path.join(utils.get_grow_dir(), 'pods', 'templates')
        jinja_env = self.pod.render_pool.custom_jinja_env(root=root)

        with jinja_env['lock']:
            if self.route_info.meta.get('template'):
                content = self.pod.read_file(self.route_info.meta['template'])
                template = jinja_env['env'].from_string(content)
            else:
                template = jinja_env['env'].get_template('sitemap.xml')

            try:
                docs = []
                locales = self.route_info.meta.get('locales')
                collections = self.route_info.meta.get('collections')
                for col in list(self.pod.list_collections(collections)):
                    docs += col.list_servable_documents(locales=locales)
                rendered_doc = rendered_document.RenderedDocument(
                    self.serving_path, template.render({
                        'pod': self.pod,
                        'docs': docs,
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


class RenderStaticDocumentController(RenderController):
    """Controller for handling rendering for static documents."""

    def __init__(self, pod, serving_path, route_info, params=None, is_threaded=False):
        super(RenderStaticDocumentController, self).__init__(
            pod, serving_path, route_info, params=params, is_threaded=is_threaded)
        self._static_doc = None
        self._pod_path = None

    @property
    def pod_path(self):
        """Static doc for the controller."""
        if self._pod_path:
            return self._pod_path

        locale = self.route_info.meta.get(
            'locale', self.params.get('locale'))
        if 'pod_path' in self.route_info.meta:
            self._pod_path = self.route_info.meta['pod_path']
        else:
            for source_format in self.route_info.meta['source_formats']:
                path_format = '{}{}'.format(source_format, self.params['*'])
                self._pod_path = self.pod.path_format.format_static(
                    path_format, locale=locale)
                static_doc = self.pod.get_static(self._pod_path, locale=locale)
                if static_doc.exists:
                    break
                else:
                    self._pod_path = None
        return self._pod_path

    @property
    def static_doc(self):
        """Static doc for the controller."""
        if not self._static_doc:
            locale = self.route_info.meta.get(
                'locale', self.params.get('locale'))
            self._static_doc = self.pod.get_static(self.pod_path, locale=locale)
        return self._static_doc

    @property
    def mimetype(self):
        """Determine headers to serve for https requests."""
        return mimetypes.guess_type(self.serving_path)[0]

    def get_http_headers(self):
        """Determine headers to serve for http requests."""
        headers = super(RenderStaticDocumentController, self).get_http_headers()
        path = self.pod.abs_path(self.static_doc.pod_path)
        self.pod.storage.update_headers(headers, path)
        modified = self.pod.storage.modified(path)
        time_obj = datetime.datetime.fromtimestamp(modified).timetuple()
        time_format = '%a, %d %b %Y %H:%M:%S GMT'
        headers['Last-Modified'] = time.strftime(time_format, time_obj)
        headers['ETag'] = '"{}"'.format(headers['Last-Modified'])
        headers['X-Grow-Pod-Path'] = self.static_doc.pod_path
        if self.static_doc.locale:
            headers['X-Grow-Locale'] = self.static_doc.locale
        return headers

    def render(self, jinja_env=None):
        """Read the static file."""
        timer = self.pod.profile.timer(
            'RenderStaticDocumentController.render', label=self.serving_path,
            meta={'path': self.serving_path}).start_timer()

        if not self.pod.file_exists(self.pod_path):
            text = '{} was not found in static files.'
            raise errors.RouteNotFoundError(text.format(self.serving_path))

        # Validate the path with the static config specific filter.
        self.validate_path(self.route_info.meta['path_filter'])

        rendered_content = self.pod.read_file(self.pod_path)
        rendered_content = self.pod.extensions_controller.trigger(
            'post_render', self.static_doc, rendered_content)
        rendered_doc = rendered_document.RenderedDocument(
            self.serving_path, rendered_content)
        timer.stop_timer()
        return rendered_doc
