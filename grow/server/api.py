"""API Handler for serving api requests."""

import json
from werkzeug import wrappers


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
        self.data = {
            'pod_path': '/content/pages/home.yaml',
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
                        'key': 'meta.description',
                        'label': 'Description',
                    },
                    {
                        'type': 'partials',
                        'key': 'partials',
                        'label': 'Partials',
                    },
                ],
            },
            'front_matter': {
                '$title': 'Blinkk',
                '$path': '/',
                'meta': {
                    'description': 'Something really cool.',
                },
                'partials': [
                    {
                        'partial': 'hero',
                        'title': 'Blinkk',
                        'subtitle': 'New to Blinkk?',
                        'description': 'Great! This site is to help you get up to speed on how Blinkk works and some of the projects that we have going.',
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
            'serving_paths': {
                'en': '/',
            },
            'default_locale': 'en',
            'raw_front_matter': '$path: /\r$title: Something',
            'content': 'Something for content.',
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
