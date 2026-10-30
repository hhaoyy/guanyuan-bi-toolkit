"""Synthetic runtimes only; no vendor tools, network or credentials."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/guanyuan-cli/scripts/compatibility.py'
spec = importlib.util.spec_from_file_location('compatibility', SCRIPT)
compat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compat)


class CompatibilityTests(unittest.TestCase):
    def test_changed_identity_invalidates_only_affected_component(self):
        a = {'status': 'ready', 'version': '1.2.3', 'binary_sha256': 'a'}
        b = {'status': 'ready', 'version': '0.2.0', 'binary_sha256': 'b'}
        state, _ = compat.refresh({}, {'guancli': a, 'guanvis': b})
        for c in state['components'].values():
            c['adaptation'] = {'capabilities': {'read': {'status': 'documented'}}}
        unchanged, actions = compat.refresh(state, {'guancli': a})
        self.assertEqual(actions['guancli'], 'reuse_local_adaptation')
        for changed in [dict(a, version='1.2.4'), dict(a, version='1.2.2'), dict(a, binary_sha256='c'), {'status': 'missing', 'version': None}]:
            refreshed, _ = compat.refresh(state, {'guancli': changed})
            self.assertEqual(refreshed['components']['guancli']['adaptation'], {})
            self.assertEqual(refreshed['components']['guanvis'], state['components']['guanvis'])

    def test_policy_change_invalidates_cache(self):
        identity = {'status': 'ready', 'version': '1.0.0'}
        old = {'schema': 1, 'policy_revision': 0, 'components': {'guancli': {'identity': identity, 'adaptation': {'old': True}}}}
        state, _ = compat.refresh(old, {'guancli': identity})
        self.assertEqual(state['components']['guancli']['adaptation'], {})

    def test_real_subprocess_and_private_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tool = root / 'guancli'
            tool.write_text('#!' + sys.executable + '\nimport sys\nprint("guancli 1.2.3" if sys.argv[1] == "--version" else "synthetic-private-marker")\n')
            tool.chmod(0o700)
            state = root / 'local/state.json'
            command = [sys.executable, str(SCRIPT), '--components', 'guancli', '--bin-dir', tmp, '--state', str(state)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(output['components']['guancli']['version'], '1.2.3')
            self.assertNotIn('synthetic-private-marker', result.stdout + state.read_text())
            self.assertEqual(state.stat().st_mode & 0o777, 0o600)
            state.write_text('{broken')
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(state.read_text(), '{broken')

    def test_unknown_version_and_timeout_are_not_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            tool = Path(tmp) / 'guancli'
            tool.write_text('synthetic executable')
            with patch.object(compat.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'unrecognized-private-output', '')):
                result = compat.probe('guancli', tmp)
                self.assertEqual(result['status'], 'needs_inspection')
                self.assertIsNone(result['version'])
                self.assertNotIn('unrecognized-private-output', json.dumps(result))
            with patch.object(compat.subprocess, 'run', side_effect=subprocess.TimeoutExpired('synthetic', 15)):
                self.assertEqual(compat.probe('guancli', tmp)['status'], 'timeout')
            self.assertEqual(compat.probe('guanvis', tmp)['status'], 'missing')

    def test_invalid_state_rejected(self):
        with self.assertRaises(ValueError):
            compat.refresh({'schema': 99, 'components': {}}, {})
        with self.assertRaises(ValueError):
            compat.refresh({'schema': 1, 'components': {'guancli': 'invalid'}}, {})


if __name__ == '__main__':
    unittest.main()
