#!/usr/bin/env python3
"""Refresh private compatibility state from local CLI identity; never contact BI."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

COMPONENTS = ('guancli', 'guands', 'guanvis', 'guanetl', 'guanwf', 'guanmetric')
POLICY = 1
VERSION = re.compile(r'^(?:(?:@guandata/)?(?:guancli|guands|guanvis|guanetl|guanwf|guanmetric)[ :@]+)?v?(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)$')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def probe(component, bin_dir=None):
    executable = str(Path(bin_dir) / component) if bin_dir else shutil.which(component)
    if not executable or not Path(executable).is_file():
        return {'status': 'missing', 'version': None}
    try:
        binary_hash = digest(Path(executable).read_bytes())
        outputs = {}
        for flag in ('--version', '--help'):
            result = subprocess.run([executable, flag], capture_output=True, text=True,
                                    errors='replace', timeout=15)
            outputs[flag] = result
        version_result = outputs['--version']
        match = VERSION.fullmatch((version_result.stdout or '').strip()) if version_result.returncode == 0 else None
        help_result = outputs['--help']
        return {'status': 'ready' if match and help_result.returncode == 0 else 'needs_inspection',
                'version': match.group(1) if match else None,
                'binary_sha256': binary_hash,
                'help_sha256': digest((help_result.stdout or '').encode()),
                'help_exit_code': help_result.returncode}
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'version': None}
    except OSError:
        return {'status': 'launch_error', 'version': None}


def refresh(previous, observations):
    if previous and (previous.get('schema') != 1 or not isinstance(previous.get('components'), dict)):
        raise ValueError('Unsupported state schema; retain the old file and use a new state path.')
    components = dict(previous.get('components', {}))
    if any(not isinstance(value, dict) or not isinstance(value.get('adaptation', {}), dict)
           for value in components.values()):
        raise ValueError('Invalid component state; retain the old file.')
    actions = {}
    for name, observed in observations.items():
        old = components.get(name, {})
        same = (previous.get('policy_revision') == POLICY and
                observed.get('status') == 'ready' and old.get('identity') == observed)
        components[name] = {'identity': observed,
                            'adaptation': old.get('adaptation', {}) if same else {}}
        actions[name] = ('reuse_local_adaptation' if same and components[name]['adaptation']
                         else 'inspect_matching_docs' if observed.get('status') == 'ready'
                         else 'resolve_local_tool')
    return {'schema': 1, 'policy_revision': POLICY, 'components': components}, actions


def save(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.compat-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(state, stream, indent=2)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--components', nargs='+', choices=COMPONENTS, default=COMPONENTS)
    parser.add_argument('--bin-dir', help='Explicit directory of the selected runtime executables')
    parser.add_argument('--state', required=True, type=Path, help='Private project state file')
    args = parser.parse_args()
    try:
        previous = json.loads(args.state.read_text()) if args.state.exists() else {}
        if not isinstance(previous, dict):
            raise ValueError('State must be a JSON object')
        observations = {name: probe(name, args.bin_dir) for name in dict.fromkeys(args.components)}
        state, actions = refresh(previous, observations)
        save(args.state, state)
    except (OSError, ValueError, TypeError):
        print(json.dumps({'error': 'Cannot read or update state; preserve it and inspect privately.'}))
        return 2
    print(json.dumps({'components': observations, 'next_actions': actions,
                      'scope': 'Local identity only; server compatibility and publication untested.'}, indent=2))
    return 0 if all(item['status'] == 'ready' for item in observations.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
