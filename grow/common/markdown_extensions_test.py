from grow.testing import testing
from grow.pods import pods
import unittest


class CodeBlockPreprocessorTestCase(unittest.TestCase):

    def test_noclasses(self):
        pod = testing.create_pod()
        fields = {
            'markdown': {
                'extensions': [{
                    'kind': 'sourcecode',
                }],
            }
        }
        pod.write_yaml('/podspec.yaml', fields)
        fields = {
            '$view': '/views/base.html',
            '$path': '/{base}/'
        }
        pod.write_yaml('/content/pages/_blueprint.yaml', fields)
        content = """
        [sourcecode:html]
        <div class="test">
          Hello World
        </div>
        [/sourcecode]
        """
        pod.write_yaml('/content/pages/test.md', content)
        content = '{{doc.html|safe}}'
        pod.write_file('/views/base.html', content)
        controller, params = pod.match('/test/')
        result = controller.render(params)
        style_sentinel = 'style="background: #f8f8f8"'
        self.assertIn(style_sentinel, result)

        fields = {
            'markdown': {
                'extensions': [{
                    'kind': 'sourcecode',
                    'classes': True,
                }],
            }
        }
        pod.write_yaml('/podspec.yaml', fields)
        pod = pods.Pod(pod.root)
        controller, params = pod.match('/test/')
        result = controller.render(params)
        class_sentinel = '<span class="nt">'
        self.assertIn(class_sentinel, result)


if __name__ == '__main__':
    unittest.main()
