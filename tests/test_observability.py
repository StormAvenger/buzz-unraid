# SPDX-License-Identifier: MIT
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('observability', ROOT / 'rootfs/opt/buzz/buzz_observability.py')
status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(status)


class ObservabilityTests(unittest.TestCase):
    def test_readiness_requires_same_process_and_recent_event_loop(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(status.ui_ready(21, root), (False, False))
            status.write_json(root / 'heartbeat.json', {'pid': 21, 'cpu_mode': True})
            self.assertEqual(status.ui_ready(21, root), (True, True))
            self.assertFalse(status.ui_ready(22, root)[0])
            os.utime(root / 'heartbeat.json', (time.time() - 25,) * 2)
            self.assertFalse(status.ui_ready(21, root)[0])
            (root / 'heartbeat.json').write_text('not json')
            self.assertFalse(status.ui_ready(21, root)[0])

    def test_gpu_failures_never_export_raw_process_output(self):
        for output in [b'private exception /config/recording.wav', b'{"state":"checking"}', b'null',
                       b'{"state":"available","token":"secret","path":"/config/private"}']:
            process = Mock(returncode=0)
            process.poll.return_value = 0
            process.communicate.return_value = (output, None)
            result = status.finish_probe(process, 0, 1)
            self.assertEqual(set(result), {'state'})
            self.assertIn(result['state'], {'available', 'failed'})
            self.assertNotIn('secret', json.dumps(result))

    def test_gpu_probe_timeout_is_bounded_and_reaped(self):
        process = Mock()
        process.poll.return_value = None
        self.assertIsNone(status.finish_probe(process, 0, 44))
        self.assertEqual(status.finish_probe(process, 0, 46), {'state': 'timeout'})
        process.kill.assert_called_once()
        process.communicate.assert_called_once()

    def test_web_patch_fails_atomically_and_inherits_desktop_auth(self):
        spec = importlib.util.spec_from_file_location('webpatch', ROOT / 'scripts/patch-web-ui.py')
        web = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(web)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'noVNC'
            for relative, old, _ in web.PATCHES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('a') as f:
                    f.write(old + '\n')
            web.patch(root)
            server = (root / '../base/etc/nginx/default_site.conf').read_text()
            self.assertIn('location = /buzz-status.json', server)
            self.assertNotIn('auth_request off', server)
            self.assertIn('alias /tmp/buzz-status/public.json;', server)
            before = {p: p.read_bytes() for p in Path(directory).rglob('*') if p.is_file()}
            with self.assertRaises(ValueError):
                web.patch(root)
            self.assertEqual(before, {p: p.read_bytes() for p in before})


if __name__ == '__main__':
    unittest.main()
