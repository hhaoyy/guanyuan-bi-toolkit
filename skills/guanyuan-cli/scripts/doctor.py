#!/usr/bin/env python3
"""Check official CLI startup without authentication or BI mutations."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

COMPONENTS = ('guancli', 'guands', 'guanvis', 'guanetl', 'guanwf', 'guanmetric')


def inspect(component, bin_dir=None):
    executable = str(Path(bin_dir) / component) if bin_dir else shutil.which(component)
    if bin_dir and not Path(executable).is_file():
        executable = None
    if not executable:
        return {'component': component, 'status': 'missing'}
    try:
        result = subprocess.run([executable, '--help'], capture_output=True,
                                text=True, errors='replace', timeout=15)
    except subprocess.TimeoutExpired:
        return {'component': component, 'status': 'timeout'}
    except OSError:
        return {'component': component, 'status': 'launch_error'}
    # Do not print arbitrary process output or machine-specific executable paths.
    return {'component': component,
            'status': 'ready' if result.returncode == 0 else 'failed',
            'exit_code': result.returncode}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--components', nargs='+', choices=COMPONENTS, default=COMPONENTS)
    parser.add_argument('--bin-dir', help='Selected runtime bin directory; never falls back to PATH')
    args = parser.parse_args()
    results = [inspect(name, args.bin_dir) for name in dict.fromkeys(args.components)]
    print(json.dumps({'checks': results,
                      'scope': 'Local help startup only; authentication and publication untested.'},
                     indent=2))
    return 0 if all(item['status'] == 'ready' for item in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
