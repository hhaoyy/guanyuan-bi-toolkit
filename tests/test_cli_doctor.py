"""Synthetic checks; never invoke installed vendor tools or read credentials."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / 'skills/guanyuan-cli/scripts/doctor.py'
spec = importlib.util.spec_from_file_location('doctor', path)
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)


class DoctorTests(unittest.TestCase):
    def test_missing_does_not_execute(self):
        with patch.object(doctor.shutil, 'which', return_value=None), patch.object(doctor.subprocess, 'run') as run:
            self.assertEqual(doctor.inspect('guancli')['status'], 'missing')
            run.assert_not_called()

    def test_help_only_and_no_raw_output(self):
        result = subprocess.CompletedProcess([], 0, 'synthetic-private-output', '')
        with patch.object(doctor.shutil, 'which', return_value='/synthetic/guanvis'), patch.object(doctor.subprocess, 'run', return_value=result) as run:
            check = doctor.inspect('guanvis')
            self.assertEqual(check, {'component': 'guanvis', 'status': 'ready', 'exit_code': 0})
            self.assertEqual(run.call_args.args[0], ['/synthetic/guanvis', '--help'])
            self.assertEqual(run.call_args.kwargs['timeout'], 15)

    def test_failure_and_timeout_are_not_ready(self):
        with patch.object(doctor.shutil, 'which', return_value='/synthetic/guands'):
            with patch.object(doctor.subprocess, 'run', return_value=subprocess.CompletedProcess([], 2)):
                self.assertEqual(doctor.inspect('guands')['status'], 'failed')
            with patch.object(doctor.subprocess, 'run', side_effect=subprocess.TimeoutExpired('synthetic', 15)):
                self.assertEqual(doctor.inspect('guands')['status'], 'timeout')
            with patch.object(doctor.subprocess, 'run', side_effect=OSError()):
                self.assertEqual(doctor.inspect('guands')['status'], 'launch_error')


if __name__ == '__main__':
    unittest.main()
