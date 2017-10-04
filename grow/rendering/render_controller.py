"""Controller for rendering pod content."""

import mimetypes
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

    def __init__(self, pod, route_info):
        self.pod = pod
        self.route_info = route_info

    @staticmethod
    def from_route_info(pod, route_info):
        """Create the correct controller based on the route info."""
        kind = route_info.kind
        if kind == 'doc':
            return RenderDocumentController(pod, route_info)
        elif kind == 'static':
            return RenderStaticDocumentController(pod, route_info)
        elif kind == 'sitemap':
            return RenderSitemapController(pod, route_info)
        raise UnknownKindError('Do not have a controller for: {}'.format(kind))

    def get_http_headers(self):
        """Determine headers to serve for https requests."""
        headers = {}
        mimetype = self.get_mimetype()
        if mimetype:
            headers['Content-Type'] = mimetype
        return headers

    # pylint: disable=no-self-use
    def get_mimetype(self):
        """Guess the mimetype of the content."""
        return 'text/plain'

    def render(self):
        """Render the pod content."""
        raise NotImplementedError


class RenderDocumentController(RenderController):
    """Controller for handling rendering for documents."""

    @property
    def doc(self):
        """Doc for the controller."""
        pod_path = self.route_info.meta['pod_path']
        locale = self.route_info.meta['locale']
        return self.pod.get_doc(pod_path, locale=locale)

    def get_mimetype(self):
        """Determine headers to serve for https requests."""
        return mimetypes.guess_type(self.doc.view)[0]

    def render(self):
        """Render the document using the render pool."""
        doc = self.doc
        jinja_env = self.pod.render_pool.get_jinja_env(doc.locale)
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
                return rendered_document.RenderedDocument(doc.get_serving_path(),
                    template.render({
                        'doc': doc,
                        'env': self.pod.env,
                        'podspec': self.pod.podspec,
                        '_track_dependency': track_dependency,
                    }).lstrip())
            except Exception as err:
                text = 'Error building {}: {}'
                exception = errors.BuildError(text.format(self, err))
                exception.traceback = sys.exc_info()[2]
                exception.controller = self
                exception.exception = err
                if self.pod:
                    self.pod.logger.error(text.format(self, err))
                raise exception


class RenderSitemapController(RenderController):
    """Controller for handling rendering for sitemaps."""
    pass


class RenderStaticDocumentController(RenderController):
    """Controller for handling rendering for static documents."""
    pass
