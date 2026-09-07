#!/usr/bin/env python3
"""Verify the reviewed public file inventory. Never regenerate trust automatically."""
import hashlib
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'PUBLIC_FILES.sha256'


def main():
    expected = {}
    for line in (ROOT / MANIFEST).read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        digest, name = line.split('  ',1)
        if name in expected or Path(name).is_absolute() or '..' in Path(name).parts:
            raise SystemExit('Invalid manifest path')
        expected[name] = digest
    failures = []
    for name, digest in expected.items():
        path = ROOT / name
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            failures.append('Missing, changed or symbolic file: '+name)
    # Git supplies tracked and unignored files; ignored local inputs stay local.
    if (ROOT / '.git').exists():
        result = subprocess.run(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT,check=True,capture_output=True)
        actual = {s for s in result.stdout.decode().split('\0') if s}
    else:
        actual = {str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()
                  and not any(part in {'local','output','__pycache__'} for part in p.relative_to(ROOT).parts)}
    for name in sorted(actual - set(expected) - {MANIFEST}):
        failures.append('Unreviewed file: '+name)
    if failures:
        print('\n'.join(failures))
        return 1
    print(f'PASS: {len(expected)} reviewed files match SHA-256 inventory.')
    print('This verifies the reviewed snapshot, not the confidentiality of arbitrary new content.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
