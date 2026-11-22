"""Regression tests for backlog bugfixes and surgical improvements."""

import os
import tempfile
import unittest

from grow import storage
from grow.common import untag
from grow.deployments.destinations import local as local_destination
from grow.pods import pods
from grow.testing import testing
from grow.translations import importers


class BacklogBugfixesTestCase(unittest.TestCase):
    """Tests covering targeted bugfixes across routing, deploys, and translations."""

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

    def test_local_deploy_requires_out_dir(self):
        """LocalDestination raises a clear error if out_dir is omitted (#1023)."""
        dest = local_destination.LocalDestination(local_destination.Config())
        with self.assertRaises(ValueError):
            dest.prelaunch()

    def test_po_import_handles_utf8_bom_and_invalid_encoding(self):
        """Importer strips UTF-8 BOMs and reports invalid UTF-8 cleanly (#1077)."""
        importer = importers.Importer(self.pod)
        with tempfile.TemporaryDirectory() as tmp_dir:
            bom_po = os.path.join(tmp_dir, 'bom.po')
            with open(bom_po, 'wb') as fp:
                fp.write(b'\xef\xbb\xbfmsgid "Hello"\nmsgstr "Hola"\n')
            importer.import_file('es', bom_po)

            bad_po = os.path.join(tmp_dir, 'bad.po')
            with open(bad_po, 'wb') as fp:
                fp.write(b'\xff\xfeinvalid')
            with self.assertRaises(importers.Error):
                importer.import_file('es', bad_po)

    def test_extract_handles_list_yaml_and_preserves_duplicate_comments(self):
        """Extract works on list-rooted YAML files (#1022) and keeps comments (#284)."""
        self.pod.write_yaml('/content/list_data.yaml', [{'title@': 'List Item'}])
        self.pod.write_yaml('/partials/items.yaml', [{'label@': 'Partial Item'}])
        self.pod.write_yaml(
            '/content/pages/dup_a.yaml',
            {
                '$title@': 'Duplicate Greeting',
                '$title@#': 'Context for translators',
            },
        )
        self.pod.write_yaml(
            '/content/pages/dup_b.yaml',
            {
                '$title@': 'Duplicate Greeting',
            },
        )
        _, catalogs_list = self.pod.catalogs.extract(localized=False)
        catalog = catalogs_list[0]
        self.assertIn('List Item', catalog)
        self.assertIn('Partial Item', catalog)
        self.assertIn('Duplicate Greeting', catalog)
        self.assertIn('Context for translators', catalog['Duplicate Greeting'].auto_comments)

    def test_partial_build_matches_static_files(self):
        """Router.add_pod_paths includes matching static files (#1111)."""
        self.pod.router.add_pod_paths(['/static/test.txt'])
        paths = list(self.pod.router.routes.paths)
        self.assertTrue(any('/app/static/test-' in p and p.endswith('.txt') for p in paths), paths)

    def test_router_filter_supports_included_and_excluded(self):
        """Router.filter supports included/excluded aliases (#1138)."""
        self.pod.router.add_all()
        self.pod.router.filter('included', kinds=['static'])
        for _, route_info, _ in self.pod.router.routes.nodes:
            self.assertEqual(route_info.kind, 'static')

        self.pod.router.filter('excluded', kinds=['static'])
        self.assertEqual(len(list(self.pod.router.routes.paths)), 0)

    def test_untag_supports_fake_locales_case_insensitively(self):
        """Untag resolves locale-tagged keys for non-ICU/fake locales (#796)."""
        data = {
            'greeting': 'Hello',
            'greeting@es_US': 'Hola US',
            'greeting@en_xx': 'Fake Locale',
        }
        self.assertEqual(untag.Untag.untag(data, locale_identifier='es_us')['greeting'], 'Hola US')
        self.assertEqual(
            untag.Untag.untag(data, locale_identifier='en_XX')['greeting'], 'Fake Locale'
        )
