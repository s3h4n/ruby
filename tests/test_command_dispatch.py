from __future__ import annotations

import unittest
from unittest import mock

from ruby.interfaces import cli


class CommandDispatchTests(unittest.TestCase):
    def test_default_invocation_maps_to_run(self) -> None:
        with mock.patch("ruby.interfaces.cli.run_command", return_value=0) as run_cmd:
            result = cli.dispatch_command([])
        self.assertEqual(result, 0)
        run_cmd.assert_called_once()

    def test_unknown_command_prints_help_and_fails(self) -> None:
        with mock.patch("builtins.print") as mocked_print:
            result = cli.dispatch_command(["nope"])
        self.assertEqual(result, 2)
        rendered = "\n".join(str(call.args[0]) for call in mocked_print.call_args_list if call.args)
        self.assertIn("Available commands", rendered)


if __name__ == "__main__":
    unittest.main()
