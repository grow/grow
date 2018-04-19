"""API Handler for serving api requests."""

import json
import yaml
from werkzeug import wrappers
from grow.common import yaml_utils


class PodApi(object):
    """Basic pod api."""

    def __init__(self, pod, request, matched):
        self.pod = pod
        self.request = request
        self.matched = matched
        self.data = {}
        self.handle_request()

    @property
    def response(self):
        """Generate a response object from the request information."""
        return wrappers.Response(json.dumps(self.data), mimetype='application/json')

    def _load_doc(self, pod_path):
        doc = self.pod.get_doc(pod_path)
        if not doc.exists:
            return {
                'pod_path': doc.pod_path,
                'editor': doc.editor_config,
                'front_matter': {},
                'serving_paths': {},
                'default_locale': str(doc.default_locale),
                'raw_front_matter': '',
                'content': '',
            }

        serving_paths = {}
        serving_paths[str(doc.default_locale)] = doc.get_serving_path()
        for key, value in doc.get_serving_paths_localized().iteritems():
            serving_paths[str(key)] = value

        raw_front_matter = doc.format.front_matter.export()
        front_matter = yaml.load(
            raw_front_matter, Loader=yaml_utils.PlainTextYamlLoader)

        return {
            'pod_path': doc.pod_path,
            'editor': doc.editor_config,
            'front_matter': front_matter,
            'serving_paths': serving_paths,
            'default_locale': str(doc.default_locale),
            'raw_front_matter': raw_front_matter,
            'content': doc.body,
        }

    def get_editor_content(self):
        """Handle the request for editor content."""
        pod_path = self.request.params.get('pod_path')
        self.data = self._load_doc(pod_path)

    def get_partials(self):
        """Handle the request for editor content."""
        partials = {}

        for partial in self.pod.partials.get_partials():
            editor_config = partial.editor_config
            if editor_config:
                partials[partial.key] = editor_config

        self.data = {
            'partials': partials,
        }

    def handle_request(self):
        """Determine how to handle the request."""
        path = self.matched.params['path']
        method = self.request.method
        if path == 'editor/content':
            if method == 'GET':
                self.get_editor_content()
            elif method == 'POST':
                self.post_editor_content()
        elif path == 'editor/partials':
            if method == 'GET':
                self.get_partials()

    def post_editor_content(self):
        """Handle the request to save editor content."""

        pod_path = self.request.POST['pod_path']
        doc = self.pod.get_doc(pod_path)
        if 'raw_front_matter' in self.request.POST:
            doc.format.front_matter.update_raw_front_matter(
                self.request.POST['raw_front_matter'])
            doc.write()
        elif 'front_matter' in self.request.POST:
            # TODO: Array updates don't work well.
            fields = json.loads(self.request.POST['front_matter'])
            doc.format.front_matter.update_fields(fields)
            doc.write()

        self.pod.podcache.document_cache.remove(doc)
        self.data = self._load_doc(pod_path)


def serve_api(pod, request, matched, **_kwargs):
    """Serve the default console page."""
    api = PodApi(pod, request, matched)
    return api.response
