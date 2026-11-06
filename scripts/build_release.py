#!/usr/bin/env python3
"""Build a reproducible release using only the reviewed public inventory."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/guanyuan-bi/scripts'))
from package_info import inspect_bundle


def build(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?', version):
        raise ValueError('Invalid VERSION')
    if inspect_bundle(root / 'skills', version)['status'] != 'ready':
        raise ValueError('Skill versions or hashes do not match VERSION')
    inventory = {}
    for line in (root / 'PUBLIC_FILES.sha256').read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        digest, name = line.split('  ', 1)
        q = PurePosixPath(name)
        if q.is_absolute() or '..' in q.parts or '\\' in name or q.as_posix() != name or name in inventory:
            raise ValueError('Invalid public file path')
        path = root / name
        if any((root / Path(*q.parts[:i])).is_symlink() for i in range(1, len(q.parts)+1)):
            raise ValueError('Symbolic package path')
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Unreviewed contents: ' + name)
        inventory[name] = path.read_bytes()
    required = {'VERSION', 'INSTALL.md', 'LICENSE', 'README.md', 'scripts/install.py', 'scripts/check_public_files.py'}
    required.update(p.relative_to(root).as_posix() for p in (root / 'skills').rglob('*')
                    if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc' and p.name != '.DS_Store')
    if not required <= set(inventory):
        raise ValueError('Public inventory omits required installation files')
    if 'RELEASE.json' in inventory:
        raise ValueError('Build from a source checkout, not a previously generated release package')
    if (root / '.git').exists():
        if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=root).strip():
            raise ValueError('Build releases from a clean reviewed commit')
        tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')) - {''}
        if tracked != set(inventory) | {'PUBLIC_FILES.sha256'}:
            raise ValueError('Tracked files differ from the reviewed inventory')
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root).decode().strip()
    else:
        revision = 'source-archive'
    inventory['RELEASE.json'] = (json.dumps({'version': version, 'source_commit': revision}, indent=2)+'\n').encode()
    bundled_manifest = (root / 'PUBLIC_FILES.sha256').read_text(encoding='utf-8').rstrip()
    bundled_manifest += '\n' + hashlib.sha256(inventory['RELEASE.json']).hexdigest() + '  RELEASE.json\n'
    inventory['PUBLIC_FILES.sha256'] = bundled_manifest.encode()
    output.mkdir(parents=True, exist_ok=True)
    archive = output / ('guanyuan-bi-toolkit-' + version + '.zip')
    if archive.exists() or (output / 'SHA256SUMS').exists():
        raise ValueError('Release output already exists; choose an empty output directory')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, content in sorted(inventory.items()):
            info = zipfile.ZipInfo('guanyuan-bi-toolkit-' + version + '/' + name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, content)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / 'SHA256SUMS').write_text(checksum + '  ' + archive.name + '\n', encoding='utf-8')
    return {'version': version, 'source_commit': revision, 'archive': str(archive), 'sha256': checksum,
            'file_count': len(inventory)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(ROOT, args.output), indent=2))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(json.dumps({'error': str(error)}))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
