from __future__ import annotations

import unittest
from unittest import mock

from ruby.setup.doctor import run_doctor


class DoctorTests(unittest.TestCase):
    def test_doctor_reports_ollama_failure_with_remediation(self) -> None:
        with mock.patch("ruby.setup.doctor.check_ollama_tags", return_value=(False, "cannot connect")):
            report = run_doctor()
        self.assertIn("cannot connect", report)
        self.assertIn("Start Ollama", report)


if __name__ == "__main__":
    unittest.main()
