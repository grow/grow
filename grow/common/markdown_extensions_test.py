from grow.testing import testing
from grow.pods import pods
import unittest
import textwrap


class TocExtensionTestCase(unittest.TestCase):

    def test_toc(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'markdown': {
                'extensions': [{
                    'kind': 'toc',
                }],
            }
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$view': '/views/base.html',
            '$path': '/{base}/'
        })
        pod.write_file('/content/pages/test.md', textwrap.dedent(
            """\
            [TOC]
            # H1
            ## H2
            ### H3
            ## H2 A
            """))
        pod.write_file('/views/base.html', '{{doc.html|safe}}')
        controller, params = pod.match('/test/')
        result = controller.render(params)

        toc_sentinel = '<div class="toc">'
        toclink_sentinel = '<a class="toclink"'
        title_sentinel = '<span class="toctitle">toc-title</span>'
        para_sentinel = '&para;'
        sep_sentinel = 'h2_a'
        h2_sentinel = '<h2'
        self.assertIn(toc_sentinel, result)
        self.assertNotIn(title_sentinel, result)
        self.assertNotIn(toclink_sentinel, result)
        self.assertNotIn(sep_sentinel, result)
        self.assertNotIn(para_sentinel, result)
        self.assertIn(h2_sentinel, result)

        pod.write_yaml('/podspec.yaml', {
            'markdown': {
                'extensions': [{
                    'kind': 'toc',
                    'title': 'toc-title',
                    'baselevel': 3,
                    'anchorlink': True,
                    'permalink': True,
                    'separator': '_'
                }],
            }
        })
        pod = pods.Pod(pod.root)
        controller, params = pod.match('/test/')
        result = controller.render(params)
        self.assertIn(title_sentinel, result)
        self.assertNotIn(h2_sentinel, result)
        self.assertIn(toclink_sentinel, result)
        self.assertIn(sep_sentinel, result)
        self.assertIn(para_sentinel, result)


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
        pod.write_file('/content/pages/test.md', content)
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
