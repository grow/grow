"""Tests for blogger preprocessor."""

import unittest
from grow.testing import testing


class BloggerTestCase(testing.TestCase):

    def test_run(self):
        pod = testing.create_pod()
        fields = {
            'preprocessors': [{
                'name': 'blogger',
                'kind': 'blogger',
                'blog_id': '4154157974596966834',
                'collection': '/content/posts/',
                'markdown': True,
                'authenticated': False,
                'inject': True,
            }],
        }
        pod.write_yaml('/podspec.yaml', fields)
        fields = {
            '$path': '/{date}/{slug}/',
            '$view': '/views/base.html',
        }
        pod.write_yaml('/content/posts/_blueprint.yaml', fields)
        content = '{{doc.html|safe}}'
        pod.write_file('/views/base.html', content)

        # Weak test to verify preprocessor runs.
        pod.preprocess(['blogger'])

        # Verify inject.
        collection = pod.get_collection('/content/posts')
        doc = collection.docs()[0]
        preprocessor = pod.list_preprocessors()[0]
        preprocessor.inject(doc)


if __name__ == '__main__':
    unittest.main()
