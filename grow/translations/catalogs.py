"""Translation catalogs."""

from datetime import datetime
import logging
import os
import re
import textwrap
import fnmatch
from babel import util
from babel.messages import catalog
from babel.messages import mofile
from babel.messages import pofile
from babel.util import odict
from grow.pods import messages


class Catalog(catalog.Catalog):

    def __init__(self, basename='messages.po', locale=None, pod=None,
                 dir_path=None):
        dir_path = 'translations' if dir_path is None else dir_path
        self.locale = locale
        self.pod = pod
        if self.locale is None:
            self.pod_path = os.path.join(dir_path, basename)
            is_template = True
        else:
            self.pod_path = os.path.join(dir_path, str(locale), 'LC_MESSAGES',
                                         basename)
            is_template = False
        super(Catalog, self).__init__(locale=self.locale)
        if not is_template and self.exists:
            self.load()
        self._use_old_formatting = self.pod.podspec.get_config().get(
            'templates', {}).get('old_string_format', False)

    def __repr__(self):
        return '<Catalog: {}>'.format(self.pod_path)

    @property
    def mimetype(self):
        return 'text/x-gettext-translation'

    def load(self, pod_path=None):
        # Use the "pod_path" argument to load another catalog (such as a template
        # catalog) into this one.
        if pod_path is None:
            pod_path = self.pod_path
        if not self.pod.file_exists(pod_path):
            self.pod.write_file(pod_path, '')
        po_file = self.pod.open_file(pod_path)
        try:
            try:
                babel_catalog = pofile.read_po(po_file, self.locale)
            except:
                self.pod.logger.error('Error parsing catalog for: {}'.format(self.locale))
                raise
        finally:
            po_file.close()
        attr_names = [
            '_messages',
            '_num_plurals',
            '_plural_expr',
            'charset',
            'copyright_holder',
            'creation_date',
            'domain',
            'fuzzy',
            'language_team',
            'last_translator',
            'locale',
            'msgid_bugs_address',
            'obsolete',
            'project',
            'revision_date',
            'version',
        ]
        for name in attr_names:
            setattr(self, name, getattr(babel_catalog, name))

    @property
    def exists(self):
        return self.pod.file_exists(self.pod_path)

    @property
    def content(self):
        return self.pod.read_file(self.pod_path)

    def to_message(self):
        catalog_message = messages.CatalogMessage()
        catalog_message.messages = []
        for message in self:
            message_message = messages.MessageMessage()
            message_message.msgid = message.id
            message_message.msgstr = message.string
            catalog_message.messages.append(message_message)
        return catalog_message

    def save(self, include_header=False):
        if not self._use_old_formatting:
            for message in self:
                message.flags.discard('python-format')
        if not self.pod.file_exists(self.pod_path):
            self.pod.write_file(self.pod_path, '')
        outfile = self.pod.open_file(self.pod_path, mode='wb')
        Catalog.set_header_comment(self.pod, self)
        pofile.write_po(
            outfile,
            self,
            omit_header=(not include_header),
            sort_output=True,
            sort_by_file=True,
            include_previous=True,
            width=80)
        outfile.close()

    def init(self, template_path, include_header=False):
        self.load(template_path)
        self.revision_date = datetime.now(util.LOCALTZ)
        self.fuzzy = False
        self.save(include_header=include_header)

    def update_using_catalog(self, catalog_to_merge, use_fuzzy_matching=False,
                             include_obsolete=False):
        super(Catalog, self).update(
            catalog_to_merge, no_fuzzy_matching=(not use_fuzzy_matching))
        # Don't use gettext's obsolete functionality as it polutes files: merge
        # into main translations if anything
        if include_obsolete:
            self.merge_obsolete()
        self.obsolete = odict()

    def update(self, template_path=None, use_fuzzy_matching=False,
               include_obsolete=False, include_header=False):
        """Updates catalog with messages from a template."""
        if template_path is None:
            template_path = os.path.join('translations', 'messages.pot')
        if not self.exists:
            self.init(template_path)
            return
        template_file = self.pod.open_file(template_path)
        template = pofile.read_po(template_file)
        super(Catalog, self).update(
            template, no_fuzzy_matching=(not use_fuzzy_matching))
        # Don't use gettext's obsolete functionality as it polutes files: merge
        # into main translations if anything
        if include_obsolete:
            self.merge_obsolete()
        self.obsolete = odict()
        self.save(include_header=include_header)

    def merge_obsolete(self):
        """Copy obsolete terms into the main catalog."""
        for msgid, message in self.obsolete.items():
            self[msgid] = message

    @property
    def mo_path(self):
        mo_dirpath = os.path.dirname(self.pod_path)
        return os.path.join(mo_dirpath, 'messages.mo')

    @property
    def mo_modified(self):
        try:
            return self.pod.file_modified(self.mo_path)
        except OSError:
            return None

    @property
    def modified(self):
        try:
            return self.pod.file_modified(self.pod_path)
        except OSError:
            return None

    @property
    def needs_compilation(self):
        if self.mo_modified is None or self.modified is None:
            return True
        return self.modified > self.mo_modified

    def _skip_compile_error(self, error):
        # Reduces logspam by hiding errors related to placeholders.
        if (not self._use_old_formatting
            and ('incompatible format for placeholder' in str(error)
                 or 'placeholders are incompatible' in str(error))):
            return True
        return False

    def compile(self):
        self.pod.catalogs.clear_gettext_cache()
        localization = self.pod.podspec.localization
        if localization is None:
            return
        compile_fuzzy = localization.get('compile_fuzzy')
        mo_filename = self.mo_path
        num_translated = 0
        num_total = 0
        for message in list(self)[1:]:
            if message.string:
                num_translated += 1
            num_total += 1
        try:
            for message, errors in self.check():
                for error in errors:
                    if self._skip_compile_error(error):
                        continue
                    text = 'Error compiling ({}:{}): {}'
                    message = text.format(self.locale, message.lineno, error)
                    self.pod.logger.error(message)
        except IOError:
            self.pod.logger.info('Skipped catalog check for: {}'.format(self))
        text = 'Compiled: {} ({}/{})'
        self.pod.logger.info(text.format(self.locale, num_translated, num_total))
        mo_file = self.pod.open_file(mo_filename, 'wb')
        try:
            mofile.write_mo(mo_file, self, use_fuzzy=compile_fuzzy)
        finally:
            mo_file.close()

    @classmethod
    def _message_in_paths(cls, message, paths):
        location_paths = set([path for path, unused_lineno in message.locations])
        for path in paths:
            for location_path in location_paths:
                # Support pod paths and filesystem paths for tab completion.
                location_path = location_path.lstrip('/')
                path = path.lstrip('/')
                matched = fnmatch.fnmatch(location_path, path)
                if matched:
                    return True
        return False

    def list_untranslated(self, paths=None):
        """Returns untranslated messages, including fuzzy translations."""
        untranslated = []
        for message in self:
            if paths and not Catalog._message_in_paths(message, paths):
                continue
            # Ensure fuzzy messages have a message.id otherwise we'd include
            # the header as part of the results, which we don't want.
            if not message.string or (message.fuzzy and message.id):
                untranslated.append(message)
        return untranslated

    @staticmethod
    def set_header_comment(pod, catalog):
        project_title = (
            pod.yaml.get('translators', {})
            .get('project_title', 'Untitled Grow Website'))
        instructions = (
            pod.yaml.get('translators', {}).get('instructions'))
        comment = ''
        if catalog.locale:
            lang_display_name = catalog.locale.language
            comment += """
            PROJECT TITLE:
            {} ({})
            """.format(project_title, lang_display_name)
        else:
            comment += """
            PROJECT TITLE:
            {}
            """.format(project_title)
        comment = textwrap.dedent(comment)
        if instructions:
            instructions = textwrap.dedent(instructions)
            comment += """
            PROJECT INSTRUCTIONS:
            {}
            """.format(instructions)
        comment += ''
        comment = ['# {}'.format(line.lstrip()) for line in comment.split('\n')]
        comment = comment[1:]  # Strip the first blank line.
        catalog.header_comment = '\n'.join(comment)
