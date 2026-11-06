"""Installation and project lifecycle with synthetic files, no agent or BI sessions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/guanyuan-bi/scripts'))
import toolkit
from package_info import SKILLS, inspect_bundle
spec = importlib.util.spec_from_file_location('installer', ROOT / 'scripts/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def fixture(root, version='0.0.1-beta.1'):
    root.mkdir(parents=True, exist_ok=True)
    (root / 'VERSION').write_text(version)
    for name in SKILLS:
        directory = root / 'skills' / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'SKILL.md').write_text('synthetic ' + name + ' ' + version)
        if name == 'guanyuan-html-bi-generic':
            for filename in ['engine.js', 'view.js', 'theme.css']:
                p = directory / 'assets/templates' / filename
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('/* synthetic asset */')
        files = {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in directory.rglob('*') if p.is_file() and p.name != 'toolkit-manifest.json'}
        (directory / 'toolkit-manifest.json').write_text(json.dumps(
            {'schema': 1, 'skill': name, 'version': version, 'files': files}))


class ToolkitTests(unittest.TestCase):
    def test_install_repeat_upgrade_and_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / 'source'; target = root / 'agent/skills'
            fixture(source)
            result = installer.install(source, target)
            self.assertEqual(result['status'], 'installed')
            self.assertEqual(inspect_bundle(target)['status'], 'ready')
            self.assertEqual(installer.install(source, target)['status'], 'up_to_date')
            fixture(source, '0.0.2-beta.1')
            result = installer.install(source, target)
            backup = Path(result['receipt']).parent
            self.assertNotIn(target, backup.parents)
            self.assertIn('0.0.1-beta.1', (backup / 'guanyuan-bi/SKILL.md').read_text())
            self.assertIn('0.0.2-beta.1', (target / 'guanyuan-bi/SKILL.md').read_text())

    def test_modified_destination_prevents_partial_upgrade(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'source'; target=root/'agent/skills'; fixture(source)
            installer.install(source,target)
            custom=target/'guanyuan-cli/SKILL.md'; custom.write_text('user customization')
            fixture(source,'0.0.2-beta.1')
            self.assertEqual(installer.install(source,target)['status'],'conflict')
            self.assertEqual(custom.read_text(),'user customization')
            self.assertIn('0.0.1-beta.1',(target/'guanyuan-bi/SKILL.md').read_text())

    def test_failed_upgrade_restores_previous_installation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'source'; target=root/'agent/skills'; fixture(source)
            installer.install(source,target); fixture(source,'0.0.2-beta.1')
            real_replace=installer.os.replace
            def fail_once(src,dst):
                if '.guanyuan-install-' in str(src) and str(src).endswith('guanyuan-cli'):
                    raise OSError('synthetic write failure')
                return real_replace(src,dst)
            with patch.object(installer.os,'replace',side_effect=fail_once), self.assertRaises(OSError):
                installer.install(source,target)
            self.assertEqual(inspect_bundle(target,'0.0.1-beta.1')['status'],'ready')

    def test_invalid_source_and_symlinks_never_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'source'; target=root/'agent/skills'; fixture(source)
            asset=source/'skills/guanyuan-html-bi-generic/assets/templates/view.js'; asset.unlink()
            with self.assertRaises(ValueError):installer.install(source,target)
            self.assertFalse(target.exists())
            fixture(source); target.parent.mkdir(); target.symlink_to(source/'skills',target_is_directory=True)
            with self.assertRaises(ValueError):installer.install(source,target)

    def test_project_initialization_is_idempotent_and_preserves_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'source'; fixture(source)
            project=root/'my-project'
            result=toolkit.initialize(project,'overview',source/'skills')
            self.assertEqual(result['status'],'initialized')
            self.assertEqual(toolkit.project_check(project)['status'],'ready')
            self.assertIsNone(json.loads((project/'project.json').read_text())['platform']['page_id'])
            self.assertIn('false',(project/'src/data.js').read_text())
            (project/'src/data.js').write_text('user-owned project data')
            self.assertEqual(toolkit.initialize(project,'funnel',source/'skills')['status'],'existing')
            self.assertEqual((project/'src/data.js').read_text(),'user-owned project data')
            (project/'src/view.js').unlink()
            self.assertEqual(toolkit.project_check(project)['status'],'incomplete')
            occupied=root/'occupied'; occupied.mkdir(); (occupied/'keep').write_text('keep')
            with self.assertRaises(ValueError):toolkit.initialize(occupied,'overview',source/'skills')
            with self.assertRaises(ValueError):toolkit.initialize(source/'private-project','overview',source/'skills')

    def test_real_installable_bundle_and_cli_check(self):
        # Exercise actual packaged scripts in an isolated agent directory.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); target=root/'skills'; installer.install(ROOT,target)
            script=target/'guanyuan-bi/scripts/toolkit.py'
            toolbin=root/'runtime'; toolbin.mkdir(); binary=toolbin/'guancli'
            binary.write_text('#!'+sys.executable+'\nimport sys\nprint("guancli 1.2.3" if sys.argv[1]=="--version" else "synthetic help")\n')
            binary.chmod(0o700)
            result=subprocess.run([sys.executable,str(script),'check','--components','guancli','--bin-dir',str(toolbin)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            output=json.loads(result.stdout)
            self.assertEqual(output['cli']['guancli']['version'],'1.2.3')
            self.assertEqual(output['checked_skills_dir'],str(target.resolve()))
            result=subprocess.run([sys.executable,str(script),'init','--project',str(root/'project')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue((root/'project/src/view.js').is_file())
