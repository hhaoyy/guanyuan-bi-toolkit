"""Read local toolkit manifests; never access network, credentials or BI data."""
import hashlib
import json
from pathlib import Path, PurePosixPath

SKILLS = ('guanyuan-bi', 'guanyuan-html-bi-generic', 'guanyuan-metric-lineage', 'guanyuan-cli')
MARKER = 'toolkit-manifest.json'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files_in(folder):
    result = {}
    for p in folder.rglob('*'):
        relative = p.relative_to(folder)
        if '__pycache__' in relative.parts or p.name == '.DS_Store' or p.suffix == '.pyc':
            continue
        if p.is_symlink():
            raise ValueError('Symbolic links are not supported in skill contents')
        if p.is_file() and str(relative) != MARKER:
            result[relative.as_posix()] = sha256(p)
    return result


def inspect_skill(folder):
    folder = Path(folder)
    if folder.is_symlink():
        return {'status': 'conflict', 'reason': 'symbolic_skill_directory'}
    if not folder.exists():
        return {'status': 'missing'}
    try:
        marker = folder / MARKER
        if marker.is_symlink():
            raise ValueError('Symbolic manifest')
        m = json.loads(marker.read_text(encoding='utf-8'))
        if (m['schema'] != 1 or m['skill'] != folder.name or not isinstance(m['version'], str)
                or not isinstance(m['files'], dict) or 'SKILL.md' not in m['files']):
            raise ValueError('Invalid manifest')
        for name, digest in m['files'].items():
            q = PurePosixPath(name)
            if q.is_absolute() or '..' in q.parts or '\\' in name or q.as_posix() != name or name == MARKER:
                raise ValueError('Unsafe manifest path')
            if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
                raise ValueError('Invalid digest')
        actual = files_in(folder)
        missing = sorted(set(m['files']) - set(actual))
        changed = sorted(k for k in actual.keys() & m['files'].keys() if actual[k] != m['files'][k])
        extra = sorted(set(actual) - set(m['files']))
        return {'status': 'ready' if not (missing or changed or extra) else 'modified',
                'version': m['version'], 'missing': missing, 'changed': changed, 'extra': extra}
    except (OSError, ValueError, KeyError, TypeError):
        return {'status': 'unmanaged', 'reason': 'missing_or_invalid_manifest'}


def inspect_bundle(skills_dir, expected_version=None):
    checks = {name: inspect_skill(Path(skills_dir) / name) for name in SKILLS}
    versions = {r.get('version') for r in checks.values()}
    consistent = len(versions) == 1 and None not in versions
    if expected_version is not None:
        consistent = consistent and versions == {expected_version}
    return {'status': 'ready' if consistent and all(r['status'] == 'ready' for r in checks.values()) else 'needs_attention',
            'consistent_version': consistent, 'skills': checks}
