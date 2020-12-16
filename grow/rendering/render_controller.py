"""Controller for rendering pod content."""

import datetime
import mimetypes
import os
import sys
import time
from grow.common import utils
from grow.documents import static_document
from grow.pods import errors
from grow.rendering import rendered_document
from grow.templates import doc_dependency
from grow.templates import tags


class Error(Exception):
    """Base rendering pool error."""

    def __init__(self, message):
        super(Error, self).__init__(message)
        self.message = message


class UnknownKindError(Error):
    """Unknown kind of information."""
    pass


class IgnoredPathError(Error):
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
    def clean_source_dir(source_dir):
        """Clean the formatting of the source dir to format correctly."""
        source_dir = source_dir.strip()
        source_dir = source_dir.rstrip(os.path.sep)
        return source_dir

    @staticmethod
    def from_route_info(pod, serving_path, route_info, params=None):
        """Create the correct controller based on the route info."""
        if params is None:
            params = {}
        if route_info.kind == 'doc':
            return RenderDocumentController(
                pod, serving_path, route_info, params=params)
        elif route_info.kind == 'static':
            return RenderStaticDocumentController(
                pod, serving_path, route_info, params=params)
        elif route_info.kind == 'sitemap':
            return RenderSitemapController(
                pod, serving_path, route_info, params=params)
        elif route_info.kind == 'error':
            return RenderErrorController(
                pod, serving_path, route_info, params=params)
        raise UnknownKindError(
            'Do not have a controller for: {}'.format(route_info.kind))

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

    def load(self, source_dir):
        """Load the pod content from file system."""
        raise NotImplementedError

    def render(self, jinja_env, request=None):
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

    def __repr__(self):
        return '<RenderDocumentController({})>'.format(self.route_info.meta['pod_path'])

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
        if 'locale' in self.route_info.meta:
            return self.route_info.meta['locale']
        return self.doc.locale if self.doc else None

    @property
    def mimetype(self):
        """Determine headers to serve for https requests."""
        return mimetypes.guess_type(self.doc.view)[0]

    @property
    def pod_path(self):
        """Locale to use for rendering."""
        if 'pod_path' in self.route_info.meta:
            return self.route_info.meta['pod_path']
        return self.doc.pod_path if self.doc else None

    @property
    def suffix(self):
        """Determine headers to serve for https requests."""
        _, ext = os.path.splitext(self.doc.view)
        if ext == '.html':
            return 'index.html'
        return ''

    def load(self, source_dir):
        """Load the pod content from file system."""
        timer = self.pod.profile.timer(
            'RenderDocumentController.load',
            label='{} ({})'.format(self.pod_path, self.locale),
            meta={
                'path': self.pod_path,
                'locale': str(self.locale)}
        ).start_timer()

        source_dir = self.clean_source_dir(source_dir)

        # Validate the path with the config filters.
        self.validate_path()

        try:
            doc = self.doc
            serving_path = self.serving_path
            if serving_path.endswith('/'):
                serving_path = '{}{}'.format(serving_path, self.suffix)

            rendered_path = '{}{}'.format(source_dir, serving_path)
            rendered_content = self.pod.storage.read(rendered_path)

            rendered_doc = rendered_document.RenderedDocument(
                serving_path, rendered_content)
            timer.stop_timer()
            return rendered_doc
        except Exception as err:
            exception = errors.BuildError(str(err))
            exception.traceback = sys.exc_info()[2]
            exception.controller = self
            exception.exception = err
            raise exception

    def render(self, jinja_env=None, request=None):
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
            doc.footnotes.reset()
            serving_path = doc.get_serving_path()
            if serving_path.endswith('/'):
                serving_path = '{}{}'.format(serving_path, self.suffix)

            content = self.pod.extensions_controller.trigger('pre_render', doc, doc.body)
            if content:
                doc.format.update(content=content)

            rendered_content = template.render({
                'doc': doc,
                'request': request,
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
            exception = errors.BuildError(str(err))
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

    def __repr__(self):
        return '<RenderErrorController({})>'.format(self.route_info.meta['view'])

    def load(self, source_dir):
        """Load the pod content from file system."""
        timer = self.pod.profile.timer(
            'RenderErrorController.load',
            label='{} ({})'.format(
                self.route_info.meta['key'], self.route_info.meta['view']),
            meta={
                'key': self.route_info.meta['key'],
                'view': self.route_info.meta['view'],
            }
        ).start_timer()

        source_dir = self.clean_source_dir(source_dir)

        # Validate the path with the config filters.
        self.validate_path()

        try:
            serving_path = '/{}.html'.format(self.route_info.meta['key'])
            rendered_path = '{}{}'.format(source_dir, serving_path)
            rendered_content = self.pod.storage.read(rendered_path)
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

    def render(self, jinja_env=None, request=None):
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

    def load(self, source_dir):
        """Load the pod content from file system."""
        timer = self.pod.profile.timer(
            'RenderSitemapController.load',
            label='{}'.format(self.serving_path),
            meta=self.route_info.meta,
        ).start_timer()

        source_dir = self.clean_source_dir(source_dir)

        # Validate the path with the config filters.
        self.validate_path()

        try:
            rendered_path = '{}{}'.format(source_dir, self.serving_path)
            rendered_content = self.pod.storage.read(rendered_path)
            rendered_doc = rendered_document.RenderedDocument(
                self.serving_path, rendered_content)
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

    def render(self, jinja_env=None, request=None):
        """Render the document using the render pool."""
        timer = self.pod.profile.timer(
            'RenderSitemapController.render',
            label='{}'.format(self.serving_path),
            meta=self.route_info.meta,
        ).start_timer()

        # Validate the path with the config filters.
        self.validate_path()

        # Duplicate the routes to use the filters without messing up routing.
        temp_router = self.pod.router.__class__(self.pod)
        temp_router.add_all()

        # Sitemaps only show documents...?
        temp_router.filter('whitelist', kinds=['doc'])

        for sitemap_filter in self.route_info.meta.get('filters') or []:
            temp_router.filter(
                sitemap_filter['type'], collection_paths=sitemap_filter.get('collections'),
                paths=sitemap_filter.get('paths'), locales=sitemap_filter.get('locales'))

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
                for _, value, _ in temp_router.routes.nodes:
                    docs.append(self.pod.get_doc(value.meta['pod_path'], locale=value.meta['locale']))
                rendered_doc = rendered_document.RenderedDocument(
                    self.serving_path, template.render({
                        'pod': self.pod,
                        'env': self.pod.env,
                        'docs': docs,
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


class RenderStaticDocumentController(RenderController):
    """Controller for handling rendering for static documents."""

    def __init__(self, pod, serving_path, route_info, params=None, is_threaded=False):
        super(RenderStaticDocumentController, self).__init__(
            pod, serving_path, route_info, params=params, is_threaded=is_threaded)
        self._static_doc = None
        self._pod_path = None

    def __repr__(self):
        return '<RenderStaticDocumentController({})>'.format(self.route_info.meta['pod_path'])

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
                # Strip the fingerprint to get to the raw static file.
                self._pod_path = static_document.StaticDocument.strip_fingerprint(
                    self._pod_path)
                try:
                    # Throws an error when the document doesn't exist.
                    _ = self.pod.get_static(self._pod_path, locale=locale)
                    break
                except errors.DocumentDoesNotExistError:
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
        if self.pod_path is None:
            return headers
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

    def load(self, source_dir):
        """Load the pod content from file system."""
        timer = self.pod.profile.timer(
            'RenderStaticDocumentController.load', label=self.serving_path,
            meta={'path': self.serving_path}).start_timer()

        source_dir = self.clean_source_dir(source_dir)

        # Validate the path with the static config specific filter.
        self.validate_path(self.route_info.meta['path_filter'])

        rendered_path = '{}{}'.format(source_dir, self.serving_path)
        rendered_content = self.pod.storage.read(rendered_path)
        rendered_doc = rendered_document.RenderedDocument(
            self.serving_path, rendered_content)
        timer.stop_timer()
        return rendered_doc

    def render(self, jinja_env=None, request=None):
        """Read the static file."""
        timer = self.pod.profile.timer(
            'RenderStaticDocumentController.render', label=self.serving_path,
            meta={'path': self.serving_path}).start_timer()

        if not self.pod_path or not self.pod.file_exists(self.pod_path):
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
