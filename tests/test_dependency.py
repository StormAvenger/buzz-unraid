# SPDX-License-Identifier: MIT
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import types
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dependency', ROOT / 'scripts/dependency.py')
dep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dep)


class DependencyTests(unittest.TestCase):
    def record(self, key='a' * 64):
        return {'schema': 1, 'key': key, 'variant': 'cu126',
                'image': dep.IMAGE + '@sha256:' + 'b' * 64,
                'revision': 'c' * 40, 'sources': dep.WEB + dep.tag(key)}

    def test_toolbar_and_app_patches_do_not_change_dependency_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in dep.INPUTS:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            for directory in ('requirements/cu126',):
                shutil.copytree(ROOT / directory, root / directory)
            initial = dep.dependency_key(root)
            (root / 'rootfs').mkdir()
            (root / 'rootfs/toolbar.css').write_text('changed')
            (root / 'scripts/patch-buzz.py').write_text('changed')
            (root / 'LICENSE').write_text('changed app license')
            (root / 'THIRD_PARTY_NOTICES.md').write_text('changed app notice')
            (root / 'licenses').mkdir()
            (root / 'licenses/test.txt').write_text('changed app notice')
            self.assertEqual(initial, dep.dependency_key(root))
            for name in ('requirements/cu126/runtime.lock', 'Dockerfile.deps', 'requirements/cu126/os-refresh'):
                path = root / name
                original = path.read_bytes()
                path.write_bytes(b'2026-10-29\n' if name.endswith('os-refresh') else original + b'\n# input changed\n')
                self.assertNotEqual(initial, dep.dependency_key(root))
                path.write_bytes(original)

    def test_pushed_digest_comes_from_exact_repository_metadata(self):
        expected = 'sha256:' + 'b' * 64
        with patch.object(dep, 'inspect', return_value={'RepoDigests': [dep.IMAGE + '@' + expected]}):
            self.assertEqual(dep.published_digest('local-tag'), expected)
        for references in ([], [dep.IMAGE + ':latest'], ['example.org/foreign@' + expected],
                           [dep.IMAGE + '@' + expected, dep.IMAGE + '@sha256:' + 'c' * 64]):
            with self.subTest(references=references), patch.object(dep, 'inspect', return_value={'RepoDigests': references}):
                with self.assertRaises(ValueError):
                    dep.published_digest('local-tag')

    def test_mutable_foreign_or_mismatched_records_fail_closed(self):
        record = self.record()
        dep.validate_record(record, 'a' * 64)
        for field, value in [('image', dep.IMAGE + ':latest'), ('key', 'd' * 64),
                             ('variant', 'cu128'), ('sources', 'https://example.org'),
                             ('revision', 'main')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                dep.validate_record({**record, field: value}, 'a' * 64)

    def test_release_missing_never_bootstraps_production(self):
        args = types.SimpleNamespace(bootstrap=False)
        with patch.object(dep, 'approved', side_effect=dep.MissingRelease()), patch.object(dep.subprocess, 'run') as docker:
            with self.assertRaises(dep.MissingRelease):
                dep.build(args)
            docker.assert_not_called()

    def test_missing_asset_never_bootstraps_even_in_ci(self):
        error = HTTPError('https://example.org', 404, 'missing', None, None)
        with patch.object(dep, 'approved', side_effect=error), patch.object(dep.subprocess, 'run') as docker:
            with self.assertRaises(HTTPError):
                dep.build(types.SimpleNamespace(bootstrap=True))
            docker.assert_not_called()

    def test_changed_package_versions_cannot_reuse_dependency_sources(self):
        inventory = {'python': [{'name': 'Torch', 'version': '2.8.0+cu126'}],
                     'ubuntu': [{'name': 'test', 'version': '1'}], 'pyav': {'version': '19.0.2'}}
        changed = {**inventory, 'ubuntu': [{'name': 'test', 'version': '2'}]}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / 'inventory.json').write_text(json.dumps(changed))
            with patch.object(dep, 'approved', return_value=(self.record(), inventory)):
                with self.assertRaisesRegex(ValueError, 'packages differ'):
                    dep.link_sources(output)
            self.assertFalse((output / 'dependency-image.json').exists())

    def test_source_checksums_and_missing_parts_fail_closed(self):
        key = 'a' * 64
        url = dep.WEB + dep.tag(key)
        download = url.replace('/tag/', '/download/') + '/'
        inventory = {'python': [], 'ubuntu': [], 'pyav': {}}
        files = {'dependency-image.json': json.dumps(self.record()).encode(),
                 'inventory.json': json.dumps(inventory).encode(),
                 'source-manifest.json': b'{"failures": [], "archives": [{"file": "test"}]}',
                 'sources.tar.part000': b'source', 'notices.tar.gz': b'notice'}
        sums = {name: dep.hashlib.sha256(data).hexdigest() for name, data in files.items()}
        assets = [{'name': name, 'browser_download_url': download + name,
                   'digest': 'sha256:' + sums[name], 'size': len(data)} for name, data in files.items()]
        assets.append({'name': 'SHA256SUMS', 'browser_download_url': download + 'SHA256SUMS'})
        release = {'tag_name': dep.tag(key), 'draft': False, 'assets': assets}
        def fetch(address):
            if address == dep.API + '/releases/tags/' + dep.tag(key):
                return json.dumps(release).encode()
            name = address.removeprefix(download)
            if name == 'SHA256SUMS':
                return '\n'.join(digest + '  ' + name for name, digest in sums.items()).encode()
            return files[name]
        with patch.object(dep, 'get', side_effect=fetch):
            self.assertEqual(dep.approved(key)[0], self.record())
            files['inventory.json'] = b'corrupt'
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                dep.approved(key)
            files['inventory.json'] = json.dumps(inventory).encode()
            release['assets'] = [a for a in assets if a['name'] != 'sources.tar.part000']
            with self.assertRaisesRegex(ValueError, 'Missing dependency source parts'):
                dep.approved(key)
