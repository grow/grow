"""Tests for blogger preprocessor."""

import unittest
from unittest import mock

from grow.preprocessors import blogger
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

        fake_post = {
            'id': '1234567890',
            'title': 'Sample Post',
            'published': '2021-05-20T11:45:23-07:00',
            'content': '<p>Hello <strong>Blogger</strong></p>',
        }
        mock_posts = mock.MagicMock()
        mock_posts.list.return_value.execute.return_value = {'items': [dict(fake_post)]}
        mock_posts.list_next.return_value = None
        mock_posts.get.return_value.execute.return_value = dict(fake_post)
        mock_service = mock.MagicMock()
        mock_service.posts.return_value = mock_posts

        with mock.patch.object(
            blogger.BloggerPreprocessor, 'create_service', return_value=mock_service
        ):
            pod.preprocess(['blogger'])

            collection = pod.get_collection('/content/posts')
            docs = collection.docs()
            self.assertEqual(1, len(docs))
            doc = docs[0]
            self.assertEqual('Sample Post', doc.title)

            preprocessor = pod.list_preprocessors()[0]
            preprocessor.inject(doc)


if __name__ == '__main__':
    unittest.main()
