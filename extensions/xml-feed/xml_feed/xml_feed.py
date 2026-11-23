"""XML feed extension for importing RSS feeds into Grow documents."""

import collections
import email.utils
import re
import textwrap
import urllib.parse
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

import yaml
from protorpc import messages

from grow import extensions
from grow.common import structures, utils, yaml_utils
from grow.extensions import hooks

REQUEST_TIMEOUT_SECONDS = 30
_XML_DANGEROUS_DECL_RE = re.compile(rb'<!\s*(?:DOCTYPE|ENTITY)\b', re.IGNORECASE)

CONTENT_KEYS = structures.AttributeDict(
    {
        'title': 'title',
        'description': 'description',
        'link': 'link',
        'published': 'pubDate',
        'content_encoded': '{http://purl.org/rss/1.0/modules/content/}encoded',
    }
)

CONFIG_FIELDS_TO_REMOVE = [
    'field_aliases',
]


class _FirstImgSrcParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.src = None

    def handle_starttag(self, tag, attrs):
        if self.src is None and tag.lower() == 'img':
            for key, val in attrs:
                if key.lower() == 'src' and val:
                    self.src = val
                    break


def _extract_first_img_src(html_content):
    parser = _FirstImgSrcParser()
    parser.feed(html_content)
    parser.close()
    return parser.src


def _parse_pub_date(raw_date):
    if not raw_date:
        return None
    text = raw_date.strip()
    try:
        return email.utils.parsedate_to_datetime(text)
    except (TypeError, ValueError):
        pass
    try:
        normalized = text[:-1] + '+00:00' if text.endswith('Z') else text
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _sanitize_slug(slug):
    cleaned = re.sub(r'[.]{2,}', '.', slug or '')
    cleaned = re.sub(r'[.]$', '', cleaned)
    cleaned = re.sub(r'[\s/\\]', '', cleaned)
    return cleaned.strip('.')


class Article:
    """Article details parsed from an RSS feed item."""

    def __init__(self):
        self.title = None
        self.description = None
        self.image = None
        self.link = None
        self.content = None
        self.published = None
        self.slug = None
        self.fields = {}


class Options:
    def __init__(self, config):
        self.field_aliases = {}
        self._parse_config(config)

    def _parse_config(self, config):
        if 'field_aliases' in config:
            for alias, field in config['field_aliases'].items():
                self.alias_field(field, alias)

    def alias_field(self, field, alias):
        if field not in self.field_aliases:
            self.field_aliases[field] = []
        self.field_aliases[field] = self.field_aliases[field] + [alias]

    def get_aliases(self, field):
        return self.field_aliases.get(field, [])

    def get_all_aliases(self):
        all_aliases = []
        for aliases in self.field_aliases.values():
            all_aliases = all_aliases + aliases
        return all_aliases


class XmlFeedPreprocessHook(hooks.PreprocessHook):
    """Handle the preprocess hook."""

    KIND = 'xml_feed'

    class Config(messages.Message):
        """Config for XML feed preprocessing."""

        url = messages.StringField(1)
        collection = messages.StringField(2)
        field_aliases = messages.BytesField(3)

    @staticmethod
    def _download_feed(url):
        parsed = urllib.parse.urlsplit(url or '')
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            raise ValueError(f'Unsupported feed URL scheme: {url!r}')
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'grow-ext-xml-feed/2.0'},
            method='GET',
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            return resp.read()

    @classmethod
    def _parse_articles(cls, raw_feed, options):
        raw_bytes = raw_feed.encode('utf-8') if isinstance(raw_feed, str) else raw_feed
        if _XML_DANGEROUS_DECL_RE.search(raw_bytes):
            raise ValueError('XML DOCTYPE/ENTITY declarations are not permitted.')
        root = ET.fromstring(raw_bytes)

        if root.tag == 'rss':
            yield from cls._parse_articles_rss(root, options)
        else:
            raise ValueError('Only supports rss feeds currently.')

    @staticmethod
    def _parse_articles_rss(root, options):
        used_titles = set()

        for item_index, item in enumerate(root.findall('./channel/item'), start=1):
            article = Article()

            for child in item:
                if child.tag == CONTENT_KEYS.title:
                    article.title = child.text
                elif child.tag == CONTENT_KEYS.description:
                    article.description = child.text
                    if article.content is None:
                        article.content = child.text
                elif child.tag == CONTENT_KEYS.link:
                    article.link = child.text
                elif child.tag == CONTENT_KEYS.published:
                    article.published = _parse_pub_date(child.text)
                elif child.tag == CONTENT_KEYS.content_encoded:
                    article.content = child.text
                elif child.text:
                    article.fields[child.tag] = child.text

                # Handle aliases after defaults to allow overrides.
                for alias in options.get_aliases(child.tag):
                    article.fields[alias] = child.text

            base_slug = utils.slugify(article.title) if article.title else f'item-{item_index}'
            slug = _sanitize_slug(base_slug) or f'item-{item_index}'
            if slug in used_titles:
                index = 1
                alt_slug = slug
                while alt_slug in used_titles:
                    alt_slug = f'{slug}-{index}'
                    index += 1
                slug = alt_slug
            used_titles.add(slug)
            article.slug = slug

            if article.content:
                article.image = _extract_first_img_src(article.content)

            yield article

    def trigger(
        self,
        previous_result,
        config,
        names,
        tags,
        run_all,
        rate_limit,
        *_args,
        **_kwargs,
    ):
        """Execute preprocessing."""
        collection = config['collection']
        if not collection.endswith('/'):
            collection = f'{collection}/'

        options = Options(config)

        sanitized_config = {k: v for k, v in config.items() if k not in CONFIG_FIELDS_TO_REMOVE}
        sanitized_config['collection'] = collection
        config_message = self.parse_config(sanitized_config)

        raw_feed = self._download_feed(config_message.url)
        for article in self._parse_articles(raw_feed, options):
            safe_slug = _sanitize_slug(article.slug)
            if not safe_slug:
                continue
            pod_path = f'{config_message.collection}{safe_slug}.html'
            data = collections.OrderedDict()

            data['$title'] = article.title
            data['$description'] = article.description
            data['image'] = article.image
            data['published'] = article.published
            data['link'] = article.link

            for alias in options.get_all_aliases():
                data[alias] = article.fields.get(alias)

            raw_front_matter = yaml.dump(
                data,
                Dumper=yaml_utils.PlainTextYamlDumper,
                default_flow_style=False,
                allow_unicode=True,
                width=800,
            )

            raw_content = textwrap.dedent(
                """\
                {}
                ---
                {}
                """
            ).format(raw_front_matter, article.content or '')

            self.pod.logger.info(f'Saving {pod_path}')
            self.pod.write_file(pod_path, raw_content)

        return previous_result


class XmlFeedExtension(extensions.BaseExtension):
    """XML Feed import extension."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [XmlFeedPreprocessHook]
