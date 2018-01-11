# coding: utf8
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

    def test_utf8(self):
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
            # Did you see the rocket launch?
            # 로켓 발사를 봤어?
            """))
        pod.write_file('/views/base.html', '{{doc.html|safe}}')
        controller, params = pod.match('/test/')
        result = controller.render(params)

        header = '<h1 id="did-you-see-the-rocket-launch?">Did you see the rocket launch?</h1>'
        self.assertIn(header, result)

        header = u'<h1 id="로켓-발사를-봤어?">로켓 발사를 봤어?</h1>'
        self.assertIn(header, result)


class UrlPreprocessorTestCase(unittest.TestCase):

    def setUp(self):
        self.pod = testing.create_pod()
        self.pod.write_yaml('/podspec.yaml', {
            'static_dirs': [
                {
                    'static_dir': '/static/',
                    'serve_at': '/public/',
                },
            ],
        })
        self.pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$view': '/views/base.html',
            '$path': '/{base}/'
        })
        self.pod.write_file('/content/pages/test1.md', 'Testing')
        self.pod.write_file('/content/pages/test2.md', 'Testing')

    def test_url(self):
        """Plain url reference works."""
        content = 'URL:[url(\'/content/pages/test1.md\')]'
        self.pod.write_file('/content/pages/test.md', content)
        content = '{{doc.html|safe}}'
        self.pod.write_file('/views/base.html', content)
        controller, params = self.pod.match('/test/')
        result = controller.render(params)
        self.assertIn('URL:/test1', result)

    def test_url_link(self):
        """Plain url reference works."""
        content = '[Link]([url(\'/content/pages/test1.md\')])'
        self.pod.write_file('/content/pages/test.md', content)
        content = '{{doc.html|safe}}'
        self.pod.write_file('/views/base.html', content)
        controller, params = self.pod.match('/test/')
        result = controller.render(params)
        self.assertIn('href="/test1/"', result)

    def test_url_link_static(self):
        """Plain url reference works."""
        content = '[Link]([url(\'/static/test.txt\')])'
        self.pod.write_file('/content/pages/test.md', content)
        content = '{{doc.html|safe}}'
        self.pod.write_file('/views/base.html', content)
        controller, params = self.pod.match('/test/')
        result = controller.render(params)
        self.assertIn('href="/public/test.txt"', result)

    def test_url_link_multiple(self):
        """Plain url reference works."""
        content = ('[Link]([url(\'/content/pages/test1.md\')])'
                   '[Link]([url(\'/content/pages/test2.md\')])')
        self.pod.write_file('/content/pages/test.md', content)
        content = '{{doc.html|safe}}'
        self.pod.write_file('/views/base.html', content)
        controller, params = self.pod.match('/test/')
        result = controller.render(params)
        self.assertIn('href="/test1/"', result)
        self.assertIn('href="/test2/"', result)


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

        # Verify no language.
        content = """
        [sourcecode]
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
                    'highlighter': 'plain',
                    'classes': True,
                }],
            }
        }
        pod.write_yaml('/podspec.yaml', fields)
        pod = pods.Pod(pod.root)
        controller, params = pod.match('/test/')
        result = controller.render(params)
        code_sentinel = '<div class="code"><pre>'
        self.assertIn(code_sentinel, result)

class BacktickPreprocessorTestCase(unittest.TestCase):

    def test_noclasses(self):
        pod = testing.create_pod()
        fields = {
            'markdown': {
                'extensions': [{
                    'kind': 'markdown.extensions.codehilite',
                }],
            }
        }
        pod.write_yaml('/podspec.yaml', fields)
        fields = {
            '$view': '/views/base.html',
            '$path': '/{base}/'
        }
        pod.write_yaml('/content/pages/_blueprint.yaml', fields)
        content = '{{doc.html|safe}}'
        pod.write_file('/views/base.html', content)

        # Verify ticks.
        content = textwrap.dedent(
            """
            ```html
            <div class="test">
              Hello World
            </div>
            ```
            """)
        pod.write_file('/content/pages/test.md', content)
        controller, params = pod.match('/test/')
        result = controller.render(params)
        style_sentinel = 'style="background: #f8f8f8"'
        self.assertIn(style_sentinel, result)

        fields = {
            'markdown': {
                'extensions': [{
                    'kind': 'markdown.extensions.codehilite',
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
