from . import utils
from markdown import extensions
from markdown import preprocessors
from markdown.extensions import toc
from protorpc import messages
from protorpc import protojson
from pygments import highlight
from pygments import lexers
from pygments.formatters import html
from pygments.lexers import TextLexer
from pygments.lexers import get_lexer_by_name
import json
import re


def config_from_json(config_class, config):
    config = json.dumps(config)
    return protojson.decode_message(config_class, config)


def get_config(kind, config_class, pod):
    config = config_class()
    if 'markdown' in pod.podspec:
        markdown = pod.podspec.markdown
        if 'extensions' in markdown:
            for extension in markdown['extensions']:
                if extension.get('kind', '') != kind:
                    continue
                return config_from_json(config_class, extension)
    return config


class TocExtension(toc.TocExtension):
    KIND = 'toc'

    class Config(messages.Message):
        marker = messages.StringField(1)
        title = messages.StringField(2)
        baselevel = messages.IntegerField(3)
        anchorlink = messages.BooleanField(4)
        permalink = messages.BooleanField(5)
        separator = messages.StringField(6)

    def __init__(self, pod):
        config = get_config(TocExtension.KIND, TocExtension.Config, pod)
        config_kwargs = {}
        for item in config.all_fields():
            val = config.get_assigned_value(item.name)
            if val is not None:
                config_kwargs[item.name] = val
        configs = config_kwargs.items()
        # HTML5 allows all non-space characters for a valid id.
        configs += [(
            'slugify',
            lambda value, separator: separator.join(value.split()).lower()
        )]
        super(TocExtension, self).__init__ (configs=configs)


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
    pattern_tag = re.compile(r'\[sourcecode(:.*?)\](.+?)\[/sourcecode\]', re.S)
    pattern_ticks = re.compile(r'```(.+?)\n(.+?)\n```', re.S)

    class Config(messages.Message):
        classes = messages.BooleanField(1, default=False)
        class_name = messages.StringField(2, default='code')
        highlighter = messages.StringField(3, default='pygments')

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
        return get_config(
            CodeBlockPreprocessor.KIND,
            CodeBlockPreprocessor.Config, self.pod)

    def run(self, lines):
        class_name = self.config.class_name
        def repl(m):
            language = m.group(1)
            language = language[1:] if language[0] == ':' else language
            if language in ['', 'none']:
                language = 'text'
            content = m.group(2)
            if self.config.highlighter == 'pygments':
                try:
                    lexer = lexers.get_lexer_by_name(language)
                except ValueError:
                    lexer = lexers.TextLexer()
                code = highlight(content, lexer, self.formatter)
                return '\n\n<div class="%s">%s</div>\n\n' % (class_name, code)
            elif self.config.highlighter == 'plain':
                return '\n\n<pre><code class="%s">%s</code></pre>\n\n' \
                    % (language, content)
            text = '{} is an invalid highlighter. Valid choices are: pygments, plain.'
            raise ValueError(text.format(self.config.highlighter))
        content = '\n'.join(lines)
        content = self.pattern_tag.sub(repl, content)
        content = self.pattern_ticks.sub(repl, content)
        return content.split('\n')


class CodeBlockExtension(extensions.Extension):

    def __init__(self, pod):
        self.pod = pod

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.processor = CodeBlockPreprocessor(self.pod, md)
        self.processor.md = md
        md.preprocessors.add('sourcecode', self.processor, '_begin')
