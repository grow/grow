from . import catalogs
from . import importers
from babel import support
from babel import util as babel_util
from babel.messages import catalog
from babel.messages import catalog as babel_catalog
from babel.messages import extract
from babel.messages import pofile
from grow.common import utils
from grow.pods import messages
import click
import collections
import gettext
import os
import tokenize


_TRANSLATABLE_EXTENSIONS = (
    '.html',
    '.md',
    '.yaml',
    '.yml',
)


class Error(Exception):
    pass


class UsageError(Error, click.UsageError):
    pass


class Catalogs(object):
    root = '/translations'

    def __init__(self, pod, template_path=None):
        self.pod = pod
        self._gettext_translations = {}
        if template_path:
            self.template_path = template_path
        else:
            self.template_path = os.path.join(Catalogs.root, 'messages.pot')

    def get(self, locale, basename='messages.po', dir_path=None):
        return catalogs.Catalog(basename, locale, pod=self.pod, dir_path=dir_path)

    def get_template(self, basename='messages.pot'):
        return catalogs.Catalog(basename, None, pod=self.pod)

    def list_locales(self):
        locales = set()
        for path in self.pod.list_dir(Catalogs.root):
            parts = path.split('/')
            if len(parts) > 2:
                locales.add(parts[1])
        return list(locales)

    def validate_locales(self, locales):
        for locale in locales:
            if '_' in locale:
                parts = locale.split('_')
                territory = parts[-1]
                if territory != territory.upper():
                    parts[-1] = territory.upper()
                    correct_locale = '_'.join(parts)
                    text = 'WARNING: Translation directories are case sensitive (move {} -> {}).'
                    self.pod.logger.warning(text.format(locale, correct_locale))

    def __iter__(self):
        for locale in self.list_locales():
            yield self.get(locale)

    def __len__(self):
        return len([catalog for catalog in self])

    def compile(self, force=False):
        self.clear_gettext_cache()
        locales = self.list_locales()
        self.validate_locales(locales)
        for locale in locales:
            catalog = self.get(locale)
            if not catalog.exists:
                self.pod.logger.info('Does not exist: {}'.format(catalog))
                continue
            if force or catalog.needs_compilation:
                catalog.compile()

    def to_message(self):
        message = messages.CatalogsMessage()
        message.catalogs = []
        for locale in self.list_locales():
            catalog = self.get(locale)
            message.catalogs.append(catalog.to_message())
        return message

    def init(self, locales, include_header=False):
        for locale in locales:
            catalog = self.get(locale)
            catalog.init(template_path=self.template_path,
                         include_header=include_header)

    def update(self, locales, use_fuzzy_matching=False, include_header=False):
        for locale in locales:
            catalog = self.get(locale)
            self.pod.logger.info('Updating: {}'.format(locale))
            catalog.update(template_path=self.template_path,
                           use_fuzzy_matching=use_fuzzy_matching,
                           include_header=include_header)

    def import_translations(self, path=None, locale=None, content=None):
        importer = importers.Importer(self.pod)
        if path:
            importer.import_path(path, locale=locale)
        if content:
            importer.import_content(content=content, locale=locale)

    def _get_or_create_catalog(self, template_path):
        exists = True
        if not self.pod.file_exists(template_path):
            self.pod.write_file(template_path, '')
            exists = False
        catalog = pofile.read_po(self.pod.open_file(template_path))
        return catalog, exists

    def _add_message(self, catalog, message):
        lineno, string, comments, context = message
        flags = set()
        if string in catalog:
            existing_message = catalog.get(string)
            flags = existing_message.flags
        return catalog.add(string, None, auto_comments=comments, context=context,
                           flags=flags)

    def _should_extract_as_csv(self, given_paths, path):
        ext = os.path.splitext(path)[-1]
        if ext != '.csv':
            return False
        return given_paths is None or path in given_paths

    def _should_extract_as_babel(self, given_paths, path):
        if os.path.splitext(path)[-1] not in _TRANSLATABLE_EXTENSIONS:
            return False
        return not given_paths or path in given_paths

    def extract(self, include_obsolete=False, localized=False, paths=None,
                include_header=False, locales=None, use_fuzzy_matching=False):
        env = self.pod.get_jinja_env()

        all_locales = set(list(self.pod.list_locales()))
        message_ids_to_messages = {}
        paths_to_messages = collections.defaultdict(set)
        paths_to_locales = collections.defaultdict(set)

        comment_tags = [
            ':',
        ]
        options = {
            'extensions': ','.join(env.extensions.keys()),
            'silent': 'false',
        }

        # Extract from content files.
        def callback(doc, item, key, unused_node):
            # Verify that the fields we're extracting are fields for a document
            # that's in the default locale. If not, skip the document.
            _handle_field(doc.pod_path, item, key, unused_node)

        def _add_existing_message(msgid, locations, auto_comments=None,
                                  context=None, path=None):
            existing_message = message_ids_to_messages.get(msgid)
            auto_comments = [] if auto_comments is None else auto_comments
            if existing_message:
                message_ids_to_messages[msgid].locations.extend(locations)
                paths_to_messages[path].add(existing_message)
            else:
                message = catalog.Message(
                    msgid,
                    None,
                    auto_comments=auto_comments,
                    context=context,
                    locations=locations)
                paths_to_messages[path].add(message)
                message_ids_to_messages[message.id] = message

        def _handle_field(path, item, key, node):
            if (not key
                    or not isinstance(item, basestring)
                    or not isinstance(key, basestring)
                    or not key.endswith('@')):
                return
            # Support gettext "extracted comments" on tagged fields. This is
            # consistent with extracted comments in templates, which follow
            # the format "{#: Extracted comment. #}". An example:
            #   field@: Message.
            #   field@#: Extracted comment for field@.
            auto_comments = []
            if isinstance(node, dict):
                auto_comment = node.get('{}#'.format(key))
                if auto_comment:
                    auto_comments.append(auto_comment)
            locations = [(path, 0)]
            _add_existing_message(
                msgid=item,
                auto_comments=auto_comments,
                locations=locations,
                path=path)

        for collection in self.pod.list_collections():
            text = 'Extracting collection: {}'.format(collection.pod_path)
            self.pod.logger.info(text)
            # Extract from blueprint.
            utils.walk(collection.tagged_fields, lambda *args: callback(collection, *args))
            # Extract from docs in collection.
            for doc in collection.docs(include_hidden=True):
                if not self._should_extract_as_babel(paths, doc.pod_path):
                    continue
                tagged_fields = doc.get_tagged_fields()
                utils.walk(tagged_fields, lambda *args: callback(doc, *args))
                paths_to_locales[doc.pod_path].update(doc.locales)
                all_locales.update(doc.locales)

        # Extract from podspec.
        config = self.pod.get_podspec().get_config()
        podspec_path = '/podspec.yaml'
        if self._should_extract_as_babel(paths, podspec_path):
            self.pod.logger.info('Extracting podspec: {}'.format(podspec_path))
            utils.walk(config, lambda *args: _handle_field(podspec_path, *args))

        # Extract from content and views.
        pod_files = [os.path.join('/views', path)
                     for path in self.pod.list_dir('/views/')]
        pod_files += [os.path.join('/content', path)
                      for path in self.pod.list_dir('/content/')]
        pod_files += [os.path.join('/data', path)
                      for path in self.pod.list_dir('/data/')]
        for pod_path in pod_files:
            if self._should_extract_as_csv(paths, pod_path):
                rows = utils.get_rows_from_csv(self.pod, pod_path)
                self.pod.logger.info('Extracting: {}'.format(pod_path))
                for row in rows:
                    for i, parts in enumerate(row.iteritems()):
                        key, val = parts
                        if key.endswith('@'):
                            locations = [(pod_path, i)]
                            _add_existing_message(
                                msgid=val,
                                locations=locations,
                                path=pod_path)
            elif self._should_extract_as_babel(paths, pod_path):
                if pod_path.startswith('/data') and pod_path.endswith(('.yaml', '.yml')):
                    self.pod.logger.info('Extracting: {}'.format(pod_path))
                    content = self.pod.read_file(pod_path)
                    fields = utils.load_yaml(content, pod=self.pod)
                    utils.walk(fields, lambda *args: _handle_field(pod_path, *args))
                    continue

                pod_locales = paths_to_locales.get(pod_path)
                if pod_locales:
                    text = 'Extracting: {} ({} locales)'
                    text = text.format(pod_path, len(pod_locales))
                    self.pod.logger.info(text)
                else:
                    self.pod.logger.info('Extracting: {}'.format(pod_path))
                fp = self.pod.open_file(pod_path)
                try:
                    all_parts = extract.extract(
                        'jinja2.ext.babel_extract', fp, options=options,
                        comment_tags=comment_tags)
                    for parts in all_parts:
                        lineno, string, comments, context = parts
                        locations = [(pod_path, lineno)]
                        _add_existing_message(
                            msgid=string,
                            auto_comments=comments,
                            context=context,
                            locations=locations,
                            path=pod_path)
                except tokenize.TokenError:
                    self.pod.logger.error('Problem extracting: {}'.format(pod_path))
                    raise

        # Localized message catalogs.
        if localized:
            for locale in all_locales:
                if locales and locale not in locales:
                    continue
                localized_catalog = self.get(locale)
                if not include_obsolete:
                    localized_catalog.obsolete = babel_util.odict()
                    for message in list(localized_catalog):
                        if message.id not in message_ids_to_messages:
                            localized_catalog.delete(message.id, context=message.context)

                catalog_to_merge = catalog.Catalog()
                for path, message_items in paths_to_messages.iteritems():
                    locales_with_this_path = paths_to_locales.get(path)
                    if locales_with_this_path and locale not in locales_with_this_path:
                        continue
                    for message in message_items:
                        translation = None
                        existing_message = localized_catalog.get(message.id)
                        if existing_message:
                            translation = existing_message.string
                        catalog_to_merge.add(
                            message.id, translation, locations=message.locations,
                            auto_comments=message.auto_comments, flags=message.flags,
                            user_comments=message.user_comments, context=message.context,
                            lineno=message.lineno, previous_id=message.previous_id)

                localized_catalog.update_using_catalog(
                    catalog_to_merge, use_fuzzy_matching=use_fuzzy_matching)
                localized_catalog.save(include_header=include_header)
                missing = localized_catalog.list_untranslated()
                num_messages = len(localized_catalog)
                num_translated = num_messages - len(missing)
                text = 'Saved: /{path} ({num_translated}/{num_messages})'
                self.pod.logger.info(
                    text.format(path=localized_catalog.pod_path,
                                num_translated=num_translated,
                                num_messages=num_messages))
            return

        # Global (or missing, specified by -o) message catalog.
        template_path = self.template_path
        catalog_obj, _ = self._get_or_create_catalog(template_path)
        if not include_obsolete:
            catalog_obj.obsolete = babel_util.odict()
            for message in list(catalog_obj):
                catalog_obj.delete(message.id, context=message.context)
        for message in message_ids_to_messages.itervalues():
            if message.id:
                catalog_obj.add(message.id, None, locations=message.locations,
                                auto_comments=message.auto_comments)
        return self.write_template(
            template_path, catalog_obj, include_obsolete=include_obsolete,
            include_header=include_header)

    def write_template(self, template_path, catalog, include_obsolete=False,
                       include_header=False):
        template_file = self.pod.open_file(template_path, mode='w')
        catalogs.Catalog.set_header_comment(self.pod, catalog)
        pofile.write_po(
            template_file, catalog, width=80, omit_header=(not include_header),
            sort_output=True, sort_by_file=True,
            ignore_obsolete=(not include_obsolete))
        text = 'Saved: {} ({} messages)'
        self.pod.logger.info(text.format(template_path, len(catalog)))
        template_file.close()
        return catalog

    def find_mo_file(self, locale):
        identifiers = gettext._expand_lang(str(locale))
        for identifier in identifiers:
            path = os.path.join(
                '/translations', identifier, 'LC_MESSAGES',
                'messages.mo')
            try:
                return path, self.pod.open_file(path)
            except IOError:
                pass
        return None, None

    def clear_gettext_cache(self):
        self._gettext_translations = {}

    def get_gettext_translations(self, locale):
        if locale in self._gettext_translations:
            return self._gettext_translations[locale]
        path, fp = self.find_mo_file(locale)
        if fp:
            trans = support.Translations(fp, domain='messages')
        else:
            trans = support.NullTranslations()
        self._gettext_translations[locale] = trans
        return trans

    def filter(self, out_path=None, out_dir=None,
               include_obsolete=True, localized=False,
               paths=None, include_header=None, locales=None):
        if localized and out_dir is None:
            raise UsageError('Must specify --out_dir when using --localized in '
                             'order to generate localized catalogs.')
        if not localized and out_path is None:
            raise UsageError('Must specify -o when not using --localized.')
        filtered_catalogs = []
        messages_to_locales = collections.defaultdict(list)
        for locale in locales:
            locale_catalog = self.get(locale)
            missing_messages = locale_catalog.list_untranslated(paths=paths)
            num_missing = len(missing_messages)
            num_total = len(locale_catalog)
            for message in missing_messages:
                messages_to_locales[message].append(locale_catalog.locale)
            # Generate localized catalogs.
            if localized:
                filtered_catalog = self.get(locale, dir_path=out_dir)
                for message in missing_messages:
                    filtered_catalog[message.id] = message
                if len(filtered_catalog):
                    text = 'Saving: {} ({} missing of {})'
                    text = text.format(filtered_catalog.pod_path, num_missing,
                                       num_total)
                    self.pod.logger.info(text)
                    filtered_catalog.save(include_header=include_header)
                else:
                    text = 'Skipping: {} (0 missing of {})'
                    text = text.format(filtered_catalog.pod_path, num_total)
                    self.pod.logger.info(text)
                filtered_catalogs.append(filtered_catalog)
        if localized:
            return filtered_catalogs
        # Generate a single catalog template.
        self.pod.write_file(out_path, '')
        babel_catalog = pofile.read_po(self.pod.open_file(out_path))
        for message in messages_to_locales.keys():
            babel_catalog[message.id] = message
        self.write_template(out_path, babel_catalog,
                            include_header=include_header)
        return [babel_catalog]
