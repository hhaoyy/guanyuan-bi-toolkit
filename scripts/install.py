#!/usr/bin/env python3
"""Install the four reviewed skills without overwriting local modifications."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/guanyuan-bi/scripts'))
from package_info import SKILLS, inspect_bundle, inspect_skill


def install(source, target):
    source, target = Path(source).resolve(), Path(target).expanduser()
    if target.is_symlink():
        raise ValueError('Skills directory is a symbolic link; choose its explicit destination.')
    target = target.resolve()
    if target == source or source in target.parents or target in source.parents:
        raise ValueError('Install outside the source package.')
    version = (source / 'VERSION').read_text(encoding='utf-8').strip()
    bundle = inspect_bundle(source / 'skills', version)
    if bundle['status'] != 'ready':
        raise ValueError('Source skill package is incomplete or modified; use a verified release.')
    current = {name: inspect_skill(target / name) for name in SKILLS}
    conflicts = {name: state for name, state in current.items() if state['status'] not in ('ready', 'missing')}
    if conflicts:
        return {'status': 'conflict', 'changed': False, 'conflicts': conflicts,
                'next': 'Compare and merge local edits, or choose a separate skills directory. No files were replaced.'}
    # Equal version does not by itself establish equal content.
    needs = [name for name in SKILLS if current[name]['status'] == 'missing'
             or (target / name / 'toolkit-manifest.json').read_bytes()
             != (source / 'skills' / name / 'toolkit-manifest.json').read_bytes()]
    if not needs:
        return {'status': 'up_to_date', 'version': version, 'skills_dir': str(target)}
    target.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    backup = target.parent / '.guanyuan-bi-backups' / stamp
    backup.mkdir(parents=True, mode=0o700)
    receipt = {'schema': 1, 'status': 'installing', 'version': version, 'skills_dir': str(target),
               'previous': current, 'changed_skills': needs}
    receipt_path = backup / 'receipt.json'
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    moved, placed = [], []
    with tempfile.TemporaryDirectory(prefix='.guanyuan-install-', dir=target.parent) as temporary:
        stage = Path(temporary)
        for name in needs:
            shutil.copytree(source / 'skills' / name, stage / name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
        target.mkdir(exist_ok=True)
        try:
            for name in needs:
                destination = target / name
                if destination.exists():
                    os.replace(destination, backup / name)
                    moved.append(name)
                os.replace(stage / name, destination)
                placed.append(name)
            if inspect_bundle(target, version)['status'] != 'ready':
                raise ValueError('Post-install integrity check failed')
        except Exception:
            for name in reversed(placed):
                shutil.rmtree(target / name)
            for name in reversed(moved):
                os.replace(backup / name, target / name)
            receipt['status'] = 'rolled_back'
            receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
            raise
    receipt['status'] = 'complete'
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return {'status': 'installed', 'version': version, 'skills_dir': str(target), 'receipt': str(receipt_path),
            'next': 'Reload the agent skills and invoke guanyuan-bi. This does not install vendor CLI tools.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--target', choices=['codex', 'claude'])
    choice.add_argument('--skills-dir', type=Path, help='Explicit agent skill search directory')
    args = parser.parse_args()
    target = args.skills_dir or Path.home() / ('.agents/skills' if args.target == 'codex' else '.claude/skills')
    try:
        result = install(ROOT, target)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result['status'] == 'conflict' else 0
    except (OSError, ValueError) as error:
        print(json.dumps({'status': 'error', 'message': str(error)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    sys.exit(main())
