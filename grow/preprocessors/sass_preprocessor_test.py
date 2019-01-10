from grow.common import utils
from grow.testing import testing
import unittest


class SassPreprocessorTestCase(unittest.TestCase):

    def test_run(self):
        pod = testing.create_pod()
        fields = {
            'preprocessors': [{
                'name': 'sass',
                'kind': 'sass',
                'sass_dir': '/source/sass/',
                'out_dir': '/dist/css/',
            }],
        }
        pod.write_yaml('/podspec.yaml', fields)
        content = 'body\n    color: red'
        pod.write_file('/source/sass/main.sass', content)
        if utils.is_appengine():
            return
        pod.preprocess()
        result = pod.read_file('/dist/css/main.min.css')
        expected = 'body{color:red}\n'
        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
