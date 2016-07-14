from . import utils
from markdown import extensions
from markdown import preprocessors
from protorpc import messages
from pygments import highlight
from pygments import lexers
from pygments.formatters import html
from pygments.lexers import TextLexer
from pygments.lexers import get_lexer_by_name
import re


class IncludePreprocessor(preprocessors.Preprocessor):

    REGEX = re.compile("^\[include\('([^')]*)'\)\]")

    def __init__(self, pod, markdown_instance):
        self.pod = pod
        self.markdown = markdown_instance

    def run(self, lines):
        new_lines = []
        for line in lines:
            pod_paths = IncludePreprocessor.REGEX.findall(line)
            if not pod_paths or line.startswith('    '):
                new_lines.append(line)
            for pod_path in pod_paths:
                doc = self.pod.get_doc(pod_path)
                included_lines = doc.body.split('\n')
                new_lines.extend(included_lines)
        return new_lines


class IncludeExtension(extensions.Extension):

    def __init__(self, pod):
        self.pod = pod

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.processor = IncludePreprocessor(self.pod, md)
        self.processor.md = md
        # Adds the preprocessor to the beginning of the list of preprocessors.
        # https://github.com/waylan/Python-Markdown/blob/master/markdown/odict.py#L7
        md.preprocessors.add('include', self.processor, '_begin')


class UrlPreprocessor(preprocessors.Preprocessor):

    REGEX = re.compile("\[url\('([^')]*)'\)\]")

    def __init__(self, pod, markdown_instance):
        self.pod = pod
        self.markdown = markdown_instance

    def run(self, lines):
        new_lines = []
        for line in lines:
            pod_paths = UrlPreprocessor.REGEX.findall(line)
            if not pod_paths or line.startswith('    '):
                new_lines.append(line)
            else:
                for pod_path in pod_paths:
                    doc = self.pod.get_doc(pod_path)
                    line = re.sub(UrlPreprocessor.REGEX, doc.url.path, line)
                new_lines.append(line)
        return new_lines


class UrlExtension(extensions.Extension):

    def __init__(self, pod):
        self.pod = pod

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.processor = UrlPreprocessor(self.pod, md)
        self.processor.md = md
        md.preprocessors.add('url', self.processor, '_begin')


class CodeBlockPreprocessor(preprocessors.Preprocessor):
    """
    Adapted from:
    https://bitbucket.org/birkenfeld/pygments-main/ \
        src/e79a7126551c39d5f8c1b83a79c14e86992155a4/external/markdown-processor.py
    """
    KIND = 'sourcecode'
    pattern = re.compile(r'\[sourcecode:(.+?)\](.+?)\[/sourcecode\]', re.S)

    class Config(messages.Message):
        classes = messages.BooleanField(1, default=False)
        class_name = messages.StringField(2, default='code')

    def __init__(self, pod, markdown_instance):
        self.pod = pod
        self.markdown = markdown_instance

    @property
    @utils.memoize
    def formatter(self):
        return html.HtmlFormatter(noclasses=(not self.config.classes))

    @property
    @utils.memoize
    def config(self):
        # TODO: Replace with a default config parser.
        config = CodeBlockPreprocessor.Config()
        if 'markdown' in self.pod.podspec:
            markdown = self.pod.podspec.markdown
            if 'extensions' in markdown:
                for extension in markdown['extensions']:
                    if extension.get('kind') != CodeBlockPreprocessor.KIND:
                        continue
                    if 'classes' in extension:
                        config.classes = extension['classes']
                    if 'class_name' in extension:
                        config.class_name = extension['class_name']
        return config

    def run(self, lines):
        class_name = self.config.class_name
        def repl(m):
            try:
                lexer = lexers.get_lexer_by_name(m.group(1))
            except ValueError:
                lexer = lexers.TextLexer()
            code = highlight(m.group(2), lexer, self.formatter)
            return '\n\n<div class="%s">%s</div>\n\n' % (class_name, code)
        content = '\n'.join(lines)
        content = self.pattern.sub(repl, content)
        return content.split('\n')


class CodeBlockExtension(extensions.Extension):

    def __init__(self, pod):
        self.pod = pod

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.processor = CodeBlockPreprocessor(self.pod, md)
        self.processor.md = md
        md.preprocessors.add('sourcecode', self.processor, '_begin')
