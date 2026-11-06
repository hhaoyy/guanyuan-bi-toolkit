"""Verify archive boundaries, checksums and reproducibility using synthetic sources."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile
from test_toolkit import fixture

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('release_builder',ROOT/'scripts/build_release.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)


class ReleaseTests(unittest.TestCase):
    def test_only_reviewed_files_are_archived_and_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'source'; fixture(source)
            for name in ['INSTALL.md','LICENSE','README.md','scripts/install.py','scripts/check_public_files.py']:
                p=source/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('synthetic package file')
            files=sorted(p for p in source.rglob('*') if p.is_file())
            (source/'PUBLIC_FILES.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(source).as_posix()+'\n' for p in files))
            (source/'local').mkdir(); (source/'local/private.txt').write_text('synthetic excluded canary')
            a=builder.build(source,root/'one'); b=builder.build(source,root/'two')
            self.assertEqual(a['sha256'],b['sha256'])
            with zipfile.ZipFile(a['archive']) as z:
                self.assertFalse(any('private.txt' in n for n in z.namelist()))
                prefix='guanyuan-bi-toolkit-0.0.1-beta.1/'
                for line in z.read(prefix+'PUBLIC_FILES.sha256').decode().splitlines():
                    digest,name=line.split('  ',1)
                    self.assertEqual(hashlib.sha256(z.read(prefix+name)).hexdigest(),digest)
            (source/'VERSION').write_text('9.9.9')
            with self.assertRaises(ValueError):builder.build(source,root/'bad')

    def test_changed_reviewed_file_blocks_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); fixture(root)
            (root/'README.md').write_text('reviewed synthetic text')
            (root/'PUBLIC_FILES.sha256').write_text(hashlib.sha256((root/'README.md').read_bytes()).hexdigest()+'  README.md\n')
            (root/'README.md').write_text('unreviewed synthetic edit')
            with self.assertRaises(ValueError):builder.build(root,root/'output')
