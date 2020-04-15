"""Translation catalog container."""

import io
import collections
import gettext
import os
import tokenize
import texttable
from babel import support
from babel.messages import catalog as babel_catalog
from babel.messages import extract
from babel.messages import mofile
from babel.messages import pofile
import click
from grow.common import utils
from grow.pods import messages
from grow.translations import catalogs
from grow.translations import importers
from grow.translations import locales as grow_locales


_IGNORED_PREFIXS = (
    '.',
    '_',
)
_TRANSLATABLE_EXTENSIONS = (
    '.html',
    '.md',
    '.yaml',
    '.yml',
)


class Error(Exception):

    def __init__(self, message):
        super(Error, self).__init__(message)
        self.message = message


class UsageError(Error, click.UsageError):
    pass


class Catalogs(object):
    root = '/translations'

    def __init__(self, pod, template_path=None):
        self.pod = pod
        self._gettext_translations = {}
        if template_path:
            self.template_path = os.path.expanduser(template_path)
        else:
            self.template_path = os.path.join(Catalogs.root, 'messages.pot')
        self.root = os.path.dirname(self.template_path)

    def __repr__(self):
        return '<Catalogs: {}>'.format(self.template_path)

    def diff(self, other_catalogs, out_dir):
        """Produces a diff between this directory of catalogs, and another set
        of catalogs, writing the results to a directory."""
        diffed_locales_to_catalogs = collections.defaultdict(int)
        if not out_dir.endswith('messages.pot'):
            out_dir = os.path.join(out_dir, 'messages.pot')
        diffed_catalogs = self.pod.get_catalogs(out_dir)
        for this_catalog in self:
            locale = this_catalog.locale
            other_catalog = other_catalogs.get(locale, dir_path=other_catalogs.root)
            diffed_catalog = diffed_catalogs.get(locale, dir_path=diffed_catalogs.root)
            for message in this_catalog:
                # Skip empty messages.
                if not message.id:
                    continue
                # Skip messages we have in the other catalog.
                if message.id in other_catalog:
                    continue
                diffed_catalog[message.id] = message
                diffed_locales_to_catalogs[locale] += 1
            diffed_catalog.save()
        for locale, num_diff in diffed_locales_to_catalogs.items():
            self.pod.logger.info('Found different messages for {} -> {}'.format(locale, num_diff))

    def get(self, locale, basename='messages.po', dir_path=None):
        return catalogs.Catalog(basename, locale, pod=self.pod, dir_path=dir_path)

    def get_template(self, basename='messages.pot'):
        template_catalog = catalogs.Catalog(basename, None, pod=self.pod)
        if template_catalog.exists:
            template_catalog.load()
        return template_catalog

    def list_locales(self):
        locales = set()
        for path in self.pod.list_dir(self.root):
            parts = path.split('/')
            if len(parts) > 2:
                locales.add(parts[1])
        return list(locales)

    def validate_locales(self, locales):
        for locale in locales:
            parsed_locale = grow_locales.Locale.parse(locale)
            if str(parsed_locale) != locale:
                text = 'WARNING: Translation directories are case sensitive (move {} -> {}).'
                self.pod.logger.warning(text.format(locale, parsed_locale))

    def __iter__(self):
        for locale in self.list_locales():
            yield self.get(locale)

    def __len__(self):
        return len([catalog for catalog in self])

    def compile(self, force=False):
        self.clear_gettext_cache()
        locales = self.list_locales()
        self.validate_locales(locales)
        skipped_locales = []
        for locale in locales:
            catalog = self.get(locale)
            if not catalog.exists:
                skipped_locales.append(locale)
                continue
            if force or catalog.needs_compilation:
                catalog.compile()
        if skipped_locales:
            skipped_locales.sort()
            text = 'No translations to compile -> {}'
            self.pod.logger.info(text.format(', '.join(skipped_locales)))

    def to_message(self):
        message = messages.CatalogsMessage()
        message.catalogs = []
        for locale in self.list_locales():
            catalog = self.get(locale)
            message.catalogs.append(catalog.to_message())
        return message

    def get_extract_config(self, include_obsolete=None, localized=None,
                           include_header=None, use_fuzzy_matching=None):
        extract_config = self.pod.yaml.get(
            'localization', {}).get('extract', {})
        if include_obsolete is None:
            include_obsolete = extract_config.get('include_obsolete', False)
        if localized is None:
            localized = extract_config.get('localized', False)
        if include_header is None:
            include_header = extract_config.get('include_header', False)
        if use_fuzzy_matching is None:
            use_fuzzy_matching = extract_config.get('fuzzy_matching', False)
        return include_obsolete, localized, include_header, use_fuzzy_matching

    def init(self, locales, include_header=None):
        _, _, include_header, _ = \
            self.get_extract_config(include_header=include_header)
        for locale in locales:
            catalog = self.get(locale)
            catalog.init(template_path=self.template_path,
                         include_header=include_header)

    def update(self, locales, use_fuzzy_matching=None, include_header=None,
               include_obsolete=None):
        include_obsolete, _, include_header, use_fuzzy_matching = \
            self.get_extract_config(include_header=include_header,
                    include_obsolete=include_obsolete,
                    use_fuzzy_matching=use_fuzzy_matching)
        for locale in locales:
            catalog = self.get(locale)
            self.pod.logger.info('Updating: {}'.format(locale))
            catalog.update(template_path=self.template_path,
                           use_fuzzy_matching=use_fuzzy_matching,
                           include_header=include_header,
                           include_obsolete=include_obsolete)

    def import_translations(self, path=None, locale=None, content=None,
                            include_obsolete=True, untranslated=False):
        importer = importers.Importer(self.pod,
                include_obsolete=include_obsolete, untranslated=untranslated)
        if path:
            return importer.import_path(path, locale=locale)
        if content:
            return importer.import_content(content=content, locale=locale)

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

    @staticmethod
    def _starts_with_paths(paths, path):
        for prefix in paths:
            if path.startswith(prefix):
                return True
        return False

    def extract(self, include_obsolete=None, localized=None, paths=None,
                include_header=None, locales=None, use_fuzzy_matching=None,
                audit=False, out_path=None):
        include_obsolete, localized, include_header, use_fuzzy_matching, = \
            self.get_extract_config(include_header=include_header,
                                    include_obsolete=include_obsolete, localized=localized,
                                    use_fuzzy_matching=use_fuzzy_matching)

        env = self.pod.get_jinja_env()
        # {
        #    locale1: locale1_catalog,
        #    locale2: locale2_catalog,
        #    ...
        # }
        # This is built up as we extract
        localized_catalogs = {}
        untagged_strings = []
        unlocalized_catalog = catalogs.Catalog(pod=self.pod)  # for localized=False case

        comment_tags = [
            ':',
        ]
        options = {
            'extensions': ','.join(env.extensions.keys()),
            'silent': 'false',
        }

        def _add_to_catalog(message, locales):
            # Add to all relevant catalogs
            for locale in locales:
                if locale not in localized_catalogs:
                    # Start with a new catalog so we can track what's obsolete:
                    # we'll merge it with existing translations later.
                    # *NOT* setting `locale` kwarg here b/c that will load existing
                    # translations.
                    localized_catalogs[locale] = catalogs.Catalog(pod=self.pod)
                localized_catalogs[locale][message.id] = message
            unlocalized_catalog[message.id] = message

        def _handle_field(path, locales, msgid, key, node, parent_node=None):
            if (not key
                    or not isinstance(msgid, str)
                    or not isinstance(key, str)):
                return
            if not key.endswith('@'):
                if msgid:
                    untagged_strings.append((path, msgid))
                return
            # Support gettext "extracted comments" on tagged fields:
            #   field@: Message.
            #   field@#: Extracted comment for field@.
            auto_comments = []
            if isinstance(node, dict):
                auto_comment = node.get('{}#'.format(key))
                if auto_comment:
                    auto_comments.append(auto_comment)
            elif isinstance(node, list) and parent_node:
                auto_comment = parent_node.get('{}#'.format(key))
                if auto_comment:
                    auto_comments.append(auto_comment)

            message = babel_catalog.Message(
                msgid,
                None,
                auto_comments=auto_comments,
                locations=[(path, 0)])
            if msgid:
                _add_to_catalog(message, locales)

        def _babel_extract(fp, locales, path):
            try:
                all_parts = extract.extract(
                    'jinja2.ext.babel_extract',
                    fp,
                    options=options,
                    comment_tags=comment_tags)

                for parts in all_parts:
                    lineno, msgid, comments, context = parts
                    message = babel_catalog.Message(
                        msgid,
                        None,
                        auto_comments=comments,
                        locations=[(path, lineno)])
                    _add_to_catalog(message, locales)
            except tokenize.TokenError:
                self.pod.logger.error(
                    'Problem extracting body: {}'.format(path))
                raise

        # Extract from collections in /content/:
        # Strings only extracted for relevant locales, determined by locale
        # scope (pod > collection > document > document part)
        last_pod_path = None
        collection_paths = []
        for collection in self.pod.list_collections():
            collection_paths.append(collection.pod_path)

            if utils.fnmatches_paths(collection.blueprint_path, paths):
                text = 'Extracting: {}'.format(collection.blueprint_path)
                self.pod.logger.info(text)
                # Extract from blueprint.
                utils.walk(collection.tagged_fields,
                           lambda msgid, key, node, **kwargs: _handle_field(
                               collection.blueprint_path, collection.locales, msgid, key, node,
                               **kwargs))

            for doc in collection.list_docs(include_hidden=True):
                if not utils.fnmatches_paths(doc.pod_path, paths):
                    continue
                if doc.pod_path != last_pod_path:
                    self.pod.logger.info(
                        'Extracting: {} ({} locale{})'.format(
                            doc.pod_path,
                            len(doc.locales),
                            's' if len(doc.locales) != 1 else '',
                        )
                    )
                    last_pod_path = doc.pod_path

                # If doc.locale is set, this is a doc part: only extract for
                # its own locales (not those of base doc).
                if doc.locale:
                    doc_locales = [doc.locale]
                # If not is set, this is a base doc (1st or only part): extract
                # for all locales declared for this doc
                elif doc.locales:
                    doc_locales = doc.locales
                # Otherwise only include in template (--no-localized)
                else:
                    doc_locales = [None]

                doc_locales = [doc.locale]
                # Extract yaml fields: `foo@: Extract me`
                # ("tagged" = prior to stripping `@` suffix from field names)
                tagged_fields = doc.format.front_matter.raw_data
                utils.walk(tagged_fields,
                           lambda msgid, key, node, **kwargs: _handle_field(
                               doc.pod_path, doc_locales, msgid, key, node, **kwargs))

                # Extract body: {{_('Extract me')}}
                if doc.body:
                    doc_body = io.BytesIO(bytes(doc.body, 'utf-8'))
                    _babel_extract(doc_body, doc_locales, doc.pod_path)

            # Extract from CSVs for this collection's locales
            for filepath in self.pod.list_dir(collection.pod_path):
                if not utils.fnmatches_paths(filepath, paths):
                    continue
                if filepath.endswith('.csv'):
                    pod_path = os.path.join(
                        collection.pod_path, filepath.lstrip('/'))
                    self.pod.logger.info('Extracting: {}'.format(pod_path))
                    rows = self.pod.read_csv(pod_path)
                    for i, row in enumerate(rows):
                        for key, msgid in row.items():
                            _handle_field(
                                pod_path, collection.locales, msgid, key, row)

        # Extract from data directories of /content/:
        for root, dirs, _ in self.pod.walk('/content/'):
            for dir_name in dirs:
                pod_dir = os.path.join(root, dir_name)
                pod_dir = pod_dir.replace(self.pod.root, '')
                if not self._starts_with_paths(collection_paths, pod_dir):
                    for path in self.pod.list_dir(pod_dir, recursive=False):
                        if not utils.fnmatches_paths(path, paths):
                            continue

                        # Extract from non-collection csv files.
                        if path.endswith('.csv'):
                            pod_path = os.path.join(pod_dir, path.lstrip('/'))
                            self.pod.logger.info('Extracting: {}'.format(pod_path))
                            rows = self.pod.read_csv(pod_path)
                            for i, row in enumerate(rows):
                                for key, msgid in row.items():
                                    _handle_field(
                                        pod_path, self.pod.list_locales(), msgid, key, row)

                        # Extract from non-collection yaml files.
                        if path.endswith(('.yaml', '.yml')):
                            pod_path = os.path.join(pod_dir, path.lstrip('/'))
                            self.pod.logger.info('Extracting: {}'.format(pod_path))
                            utils.walk(
                                self.pod.read_yaml(pod_path),
                                lambda msgid, key, node, **kwargs: _handle_field(
                                    pod_path, self.pod.list_locales(), msgid, key, node, **kwargs)
                            )

        # Extract from data directories of /data/:
        for path in self.pod.list_dir('/data/', recursive=True):
            if not utils.fnmatches_paths(path, paths):
                continue
            if path.endswith(('.csv')):
                pod_path = os.path.join('/data/', path.lstrip('/'))
                self.pod.logger.info('Extracting: {}'.format(pod_path))
                rows = self.pod.read_csv(pod_path)
                for i, row in enumerate(rows):
                    for key, msgid in row.items():
                        _handle_field(
                            pod_path, self.pod.list_locales(), msgid, key, row)

            if path.endswith(('.yaml', '.yml')):
                pod_path = os.path.join('/data/', path.lstrip('/'))
                self.pod.logger.info('Extracting: {}'.format(pod_path))
                fields = utils.parse_yaml(
                    self.pod.read_file(pod_path), pod=self.pod)
                utils.walk(
                    fields,
                    lambda msgid, key, node, **kwargs: _handle_field(
                        pod_path, self.pod.list_locales(), msgid, key, node, **kwargs)
                )

        # Extract from root of /content/:
        for path in self.pod.list_dir('/content/', recursive=False):
            if not utils.fnmatches_paths(path, paths):
                continue
            if path.endswith(('.yaml', '.yml')):
                pod_path = os.path.join('/content/', path)
                self.pod.logger.info('Extracting: {}'.format(pod_path))
                utils.walk(
                    self.pod.get_doc(pod_path).format.front_matter.raw_data,
                    lambda msgid, key, node, **kwargs: _handle_field(
                        pod_path, self.pod.list_locales(), msgid, key, node, **kwargs)
                )

        # Extract from /views/:
        # Not discriminating by file extension, because people use all sorts
        # (htm, html, tpl, dtml, jtml, ...)
        if not audit:
            for path in self.pod.list_dir('/views/'):
                filename = os.path.basename(path)
                if not utils.fnmatches_paths(path, paths) \
                        or path.startswith(_IGNORED_PREFIXS) \
                        or filename.startswith(_IGNORED_PREFIXS):
                    continue
                pod_path = os.path.join('/views/', path)
                self.pod.logger.info('Extracting: {}'.format(pod_path))
                with self.pod.open_file(pod_path, 'rb') as f:
                    _babel_extract(f, self.pod.list_locales(), pod_path)

        # Extract from /partials/:
        if not audit:
            for path in self.pod.list_dir('/partials/'):
                filename = os.path.basename(path)
                if not utils.fnmatches_paths(path, paths) \
                        or path.startswith(_IGNORED_PREFIXS) \
                        or filename.startswith(_IGNORED_PREFIXS):
                    continue
                pod_path = os.path.join('/partials/', path)
                if path.endswith(('.yaml', '.yml')):
                    self.pod.logger.info('Extracting: {}'.format(pod_path))
                    utils.walk(
                        self.pod.get_doc(pod_path).format.front_matter.raw_data,
                        lambda msgid, key, node, **kwargs: _handle_field(
                            pod_path, self.pod.list_locales(), msgid, key, node, **kwargs)
                    )
                if path.endswith(('.html', '.htm')):
                    self.pod.logger.info('Extracting: {}'.format(pod_path))
                    with self.pod.open_file(pod_path, 'rb') as f:
                        _babel_extract(f, self.pod.list_locales(), pod_path)

        # Extract from podspec.yaml:
        if utils.fnmatches_paths('/podspec.yaml', paths):
            self.pod.logger.info('Extracting: /podspec.yaml')
            utils.walk(
                self.pod.get_podspec().get_config(),
                lambda msgid, key, node, **kwargs: _handle_field(
                    '/podspec.yaml', self.pod.list_locales(), msgid, key, node, **kwargs)
            )

        # Save it out: behavior depends on --localized and --locale flags
        # If an out path is specified, always collect strings into the one catalog.
        if localized and not out_path:
            # Save each localized catalog
            for locale, new_catalog in localized_catalogs.items():
                # Skip if `locales` defined but doesn't include this locale
                if locales and locale not in locales:
                    continue
                existing_catalog = self.get(locale)
                existing_catalog.update_using_catalog(
                    new_catalog,
                    include_obsolete=include_obsolete)
                if audit:
                    continue
                existing_catalog.save(include_header=include_header)
                missing = existing_catalog.list_untranslated()
                num_messages = len(existing_catalog)
                self.pod.logger.info(
                    'Saved: /{path} ({num_translated}/{num_messages})'.format(
                        path=existing_catalog.pod_path,
                        num_translated=num_messages - len(missing),
                        num_messages=num_messages)
                )
            return untagged_strings, localized_catalogs.items()
        else:
            # --localized omitted / --no-localized
            template_catalog = self.get_template(self.template_path)
            template_catalog.update_using_catalog(
                unlocalized_catalog,
                include_obsolete=include_obsolete)
            if not audit:
                template_catalog.save(include_header=include_header)
                text = 'Saved: {} ({} messages)'
                self.pod.logger.info(
                    text.format(template_catalog.pod_path,
                                len(template_catalog))
                )
            return untagged_strings, [template_catalog]

    def write_template(self, template_path, catalog, include_obsolete=False,
                       include_header=False):
        template_file = self.pod.open_file(template_path, mode='wb')
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
                return path, self.pod.open_file(path, 'rb')
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
        messages_to_locales = {}
        for locale in locales:
            locale_catalog = self.get(locale)
            missing_messages = locale_catalog.list_untranslated(paths=paths)
            num_missing = len(missing_messages)
            num_total = len(locale_catalog)
            for message in missing_messages:
                if message.id not in messages_to_locales:
                    messages_to_locales[message.id] = {
                        'message': message,
                        'locales': [locale_catalog.locale]
                    }
                else:
                    messages_to_locales[message.id]['locales'].append(
                        locale_catalog.locale)

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
        for message_id in messages_to_locales.keys():
            babel_catalog[message_id] = messages_to_locales[message_id]['message']
        self.write_template(out_path, babel_catalog,
                            include_header=include_header)
        return [babel_catalog]

    @classmethod
    def format_audit(cls, untagged_strings, extracted_catalogs):
        table = texttable.Texttable()
        table.set_deco(texttable.Texttable.HEADER)
        rows = []
        rows.append(['Location', 'String'])
        for location, string in untagged_strings:
            rows.append([location, string])
        table.add_rows(rows)
        content = table.draw()
        return content
