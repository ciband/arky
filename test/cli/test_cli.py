# -*- encoding: utf8 -*-
import unittest
import mock
from importlib import import_module
from arky.cli import CLI
from arky.exceptions import ParserException
from arky.rest import use as use_network


class TestCLI(unittest.TestCase):

    def test_parse(self):
        scenarios = [
            (["network"], (True, False)),
            (["account"], (True, False)),
            (["delegate"], (True, False)),
            (["ledger"], (True, False)),
        ]
        for command, expected in scenarios:
            cli = CLI()
            result = cli.parse(command)
            assert result == expected
            assert cli.module == import_module("arky.cli.{0}".format(command[0]))

    def test_parse_network(self):
        cli = CLI()
        cmd, arg = cli.parse(["network", "use", "dark"])
        assert cmd.__module__ == "arky.cli.network"
        assert cmd.__name__ == "use"
        assert arg["<name>"] == "dark"

    def test_parse_ledger_wrong_network(self):
        use_network("lisk")  # make sure to select a network on which ldgr integration doesn't work
        cli = CLI()
        result = cli.parse(["ledger"])
        assert result == (True, False)
        assert cli.module == import_module("arky.cli.ledger")
        with self.assertRaises(ParserException):
            cli.prompt
            assert cli.module == import_module("arky.cli")

    def test_parse_ledger_good_network(self):
        cli = CLI()
        cli.parse(["network", "use", "ark"])
        cmd, arg = cli.parse(["ledger", "link"])
        assert cmd.__name__ == "link"
        assert cli.module == import_module("arky.cli.ledger")

    def test_parse_back(self):
        for command in ["..", "exit"]:
            cli = CLI()
            cli.parse(["network"])
            assert cli.module == import_module("arky.cli.network")
            result = cli.parse([command])
            assert result == (True, False)
            assert cli.module == import_module("arky.cli")

    def test_parse_help(self):
        for command in ["help", "?"]:
            cli = CLI()
            with mock.patch('arky.cli.sys') as sysmock:
                result = cli.parse([command])
                assert sysmock.stdout.write.call_count == 1
            assert result == (True, False)

    def test_parse_exit(self,):
        for command in ["exit", "EXIT"]:
            cli = CLI()
            result = cli.parse([command])
            assert result == (False, False)

if __name__ == '__main__':
    unittest.main()
