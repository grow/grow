"""Extension for parsing markdown documents."""

import json
import re

from markdown import extensions, preprocessors
from markdown.extensions import toc
from protorpc import messages, protojson
from pygments import highlight, lexers
from pygments.formatters import html

from . import utils


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
        toc_depth = messages.IntegerField(7)

    def __init__(self, pod):
        config = get_config(TocExtension.KIND, TocExtension.Config, pod)
        config_kwargs = {}
        for item in config.all_fields():
            val = config.get_assigned_value(item.name)
            if val is not None:
                config_kwargs[item.name] = val
        # HTML5 allows all non-space characters for a valid id.
        config_kwargs['slugify'] = lambda value, separator: separator.join(value.split()).lower()
        super().__init__(**config_kwargs)


class IncludePreprocessor(preprocessors.Preprocessor):
    REGEX = re.compile(r"^\[include\('([^')]*)'\)\]")

    def __init__(self, pod):
        super().__init__()
        self.pod = pod

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

    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.processor = IncludePreprocessor(self.pod)
        md.preprocessors.register(self.processor, 'include', 175)


class UrlPreprocessor(preprocessors.Preprocessor):
    REGEX = re.compile(r"\[url\('([^']*)'\)\]")

    def __init__(self, pod):
        super().__init__()
        self.pod = pod

    def run(self, lines):
        new_lines = []
        for line in lines:
            pod_paths = UrlPreprocessor.REGEX.findall(line)
            if not pod_paths or line.startswith('    '):
                new_lines.append(line)
            else:
                for pod_path in pod_paths:
                    # Can not import `grow` from within extensions?
                    if pod_path.startswith('/content'):
                        doc = self.pod.get_doc(pod_path)
                    else:
                        doc = self.pod.get_static(pod_path)
                    line = re.sub(UrlPreprocessor.REGEX, doc.url.path, line, count=1)
                new_lines.append(line)
        return new_lines


class UrlExtension(extensions.Extension):
    def __init__(self, pod):
        self.pod = pod

    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.processor = UrlPreprocessor(self.pod)
        md.preprocessors.register(self.processor, 'url', 175)


class CodeBlockPreprocessor(preprocessors.Preprocessor):
    """
    Adapted from:
    https://bitbucket.org/birkenfeld/pygments-main/ \
        src/e79a7126551c39d5f8c1b83a79c14e86992155a4/external/markdown-processor.py
    """

    KIND = 'sourcecode'
    pattern_tag = re.compile(
        r'\[sourcecode(:(?P<lang>[^, \]]*))?(, hl_lines=(?P<q>[\'"])(?P<lines>[^\'"]*)(?P=q))?\](?P<content>.+?)\[/sourcecode\]',
        re.S,
    )

    class Config(messages.Message):
        classes = messages.BooleanField(1, default=False)
        class_name = messages.StringField(2, default='code')
        highlighter = messages.StringField(3, default='pygments')
        theme = messages.StringField(4, default='default')

    def __init__(self, pod):
        super().__init__()
        self.pod = pod

    @property
    @utils.memoize
    def formatter(self):
        return self.get_formatter()

    @property
    @utils.memoize
    def config(self):
        return get_config(CodeBlockPreprocessor.KIND, CodeBlockPreprocessor.Config, self.pod)

    def get_formatter(self, hl_lines=''):
        return html.HtmlFormatter(
            noclasses=(not self.config.classes),
            cssclass=self.config.class_name,
            style=self.config.theme,
            hl_lines=hl_lines,
        )

    def run(self, lines):

        def repl(m):
            language = m.group('lang')
            if language in ['', 'none']:
                language = 'text'
            hl_lines = m.group('lines')
            content = m.group('content')
            if self.config.highlighter == 'pygments':
                formatter = self.formatter
                if hl_lines:
                    formatter = self.get_formatter(hl_lines=hl_lines)
                try:
                    lexer = lexers.get_lexer_by_name(language)
                except ValueError:
                    # pylint: disable=no-member
                    lexer = lexers.TextLexer()
                return f'\n{highlight(content, lexer, formatter)}\n'
            elif self.config.highlighter == 'plain':
                text = '\n\n<div class="{}"><pre><code class="{}">{}</code></pre></div>\n\n'
                return text.format(self.config.class_name, language, content)
            text = '{} is an invalid highlighter. Valid choices are: pygments, plain.'
            raise ValueError(text.format(self.config.highlighter))

        content = '\n'.join(lines)
        content = self.pattern_tag.sub(repl, content)
        return content.split('\n')


class CodeBlockExtension(extensions.Extension):
    def __init__(self, pod):
        self.pod = pod

    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.processor = CodeBlockPreprocessor(self.pod)
        md.preprocessors.register(self.processor, 'sourcecode', 175)
