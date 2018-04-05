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

    def get_editor_content(self):
        """Handle the request for editor content."""

        doc = self.pod.get_doc(self.request.params.get('pod_path'))

        serving_paths = {}
        serving_paths[str(doc.default_locale)] = doc.get_serving_path()
        for key, value in doc.get_serving_paths_localized().iteritems():
            serving_paths[str(key)] = value

        raw_front_matter = doc.format.front_matter.export()
        front_matter = yaml.load(raw_front_matter, Loader=yaml_utils.PlainTextYamlLoader)

        self.data = {
            'pod_path': doc.pod_path,
            'editor': {
                'fields': [
                    {
                        'type': 'text',
                        'key': '$path',
                        'label': 'Serving Path',
                    },
                    {
                        'type': 'text',
                        'key': '$title',
                        'label': 'Title',
                    },
                    {
                        'type': 'textarea',
                        'key': 'description',
                        'label': 'Description',
                    },
                    {
                        'type': 'partials',
                        'key': 'partials',
                        'label': 'Partials',
                    },
                ],
            },
            'front_matter': front_matter,
            'serving_paths': serving_paths,
            'default_locale': str(doc.default_locale),
            'raw_front_matter': raw_front_matter,
            'content': doc.body,
        }

    def get_partials(self):
        """Handle the request for editor content."""
        self.data = {
            'partials': {
                'hero': {
                    'label': 'Hero',
                    'editor': {
                        'fields': [
                            {
                                'type': 'text',
                                'key': 'title',
                                'label': 'Hero Title',
                            },
                            {
                                'type': 'text',
                                'key': 'subtitle',
                                'label': 'Hero Subtitle',
                            },
                            {
                                'type': 'markdown',
                                'key': 'description',
                                'label': 'Description',
                            },
                        ],
                    },
                },
            },
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
        self.data = {
            'pod_path': '/content/pages/home.yaml',
            'front_matter': {
                '$title': 'Blinkk Team',
                '$path': '/something',
                'meta': {
                    'description': 'Something really really cool.',
                },
                'partials': [
                    {
                        'partial': 'hero',
                        'title': 'Blinkk Hero',
                        'subtitle': 'New to Blinkk saving?',
                        'description': 'Great! This changes everything.',
                        'cta': [
                            {
                                'title': 'Getting Started',
                                'url': '!g.url "/content/pages/getting-started.yaml"',
                            },
                            {
                                'title': 'Blinkk Projects',
                                'url': '!g.url "/content/pages/projects.yaml"',
                            },
                        ],
                    },
                ],
            },
            'raw_front_matter': '$path: /asdf\r$title: Other',
            'serving_paths': {
                'en': '/',
            },
            'default_locale': 'en',
        }


def serve_api(pod, request, matched, **_kwargs):
    """Serve the default console page."""
    api = PodApi(pod, request, matched)
    return api.response
