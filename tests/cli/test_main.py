#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the main command-line interface."""

import argparse
import os
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

import msgpack

from mpacklog.cli.json_printer import JSONPrinter
from mpacklog.cli.main import dump_log, get_argument_parser, main


class TestGetArgumentParser(unittest.TestCase):
    """Test argument parser creation."""

    def test_parser_creation(self):
        """Test that parser is created with expected subcommands."""
        parser = get_argument_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)

        # Test help doesn't crash
        with patch("sys.exit"):
            with patch(
                "sys.stderr",
                new_callable=StringIO,
            ), patch(
                "sys.stdout",
                new_callable=StringIO,
            ):
                parser.parse_args(["--help"])

    def test_dump_subcommand(self):
        """Test dump subcommand parsing."""
        parser = get_argument_parser()
        args = parser.parse_args(["dump", "test.log"])
        self.assertEqual(args.subcmd, "dump")
        self.assertEqual(args.logfile, "test.log")
        self.assertEqual(args.format, "json")
        self.assertFalse(args.follow)

    def test_dump_with_options(self):
        """Test dump subcommand with options."""
        parser = get_argument_parser()
        args = parser.parse_args(
            ["dump", "test.log", "field1", "field2", "--format", "csv", "-f"]
        )
        self.assertEqual(args.subcmd, "dump")
        self.assertEqual(args.logfile, "test.log")
        self.assertEqual(args.fields, ["field1", "field2"])
        self.assertEqual(args.format, "csv")
        self.assertTrue(args.follow)

    def test_list_subcommand(self):
        """Test list subcommand parsing."""
        parser = get_argument_parser()
        args = parser.parse_args(["list", "test.log"])
        self.assertEqual(args.subcmd, "list")
        self.assertEqual(args.logfile, "test.log")

    def test_serve_subcommand(self):
        """Test serve subcommand parsing."""
        parser = get_argument_parser()
        args = parser.parse_args(["serve", "/path/to/logs"])
        self.assertEqual(args.subcmd, "serve")
        self.assertEqual(args.log_path, "/path/to/logs")
        self.assertEqual(args.port, 4747)

    def test_serve_with_port(self):
        """Test serve subcommand with custom port."""
        parser = get_argument_parser()
        args = parser.parse_args(["serve", "/path/to/logs", "--port", "8080"])
        self.assertEqual(args.port, 8080)

    def test_delta_decode_subcommand(self):
        """Test delta_decode subcommand parsing."""
        parser = get_argument_parser()
        args = parser.parse_args(
            ["delta_decode", "input.mpack", "output.mpack"]
        )
        self.assertEqual(args.subcmd, "delta_decode")
        self.assertEqual(args.input_file, "input.mpack")
        self.assertEqual(args.output_file, "output.mpack")


class TestDumpLog(unittest.TestCase):
    """Test log dumping functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary log file with test data
        self.test_data = [
            {"timestamp": 1.0, "value": 42},
            {"timestamp": 2.0, "value": 43, "nested": {"key": "test"}},
        ]
        self.temp_file = tempfile.NamedTemporaryFile(mode="wb", delete=False)
        for data in self.test_data:
            packed = msgpack.packb(data)
            self.temp_file.write(packed)
        self.temp_file.close()

    def tearDown(self):
        """Clean up test fixtures."""
        os.unlink(self.temp_file.name)

    def test_dump_log_basic(self):
        """Test basic log dumping."""
        printer = JSONPrinter()
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            dump_log(self.temp_file.name, printer)

        output_lines = mock_stdout.getvalue().strip().split("\n")
        self.assertEqual(len(output_lines), 2)

    def test_dump_log_broken_pipe(self):
        """Test handling of BrokenPipeError."""
        printer = MagicMock()
        printer.process.side_effect = BrokenPipeError()

        # Should not raise an exception
        dump_log(self.temp_file.name, printer)
        printer.process.assert_called_once()


class TestMainFunction(unittest.TestCase):
    """Test main function."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary log file
        self.test_data = [{"timestamp": 1.0, "value": 42}]
        self.temp_file = tempfile.NamedTemporaryFile(mode="wb", delete=False)
        for data in self.test_data:
            packed = msgpack.packb(data)
            self.temp_file.write(packed)
        self.temp_file.close()

    def tearDown(self):
        """Clean up test fixtures."""
        os.unlink(self.temp_file.name)

    def test_main_no_args(self):
        """Test main function with no arguments."""
        with patch(
            "sys.stdout",
            new_callable=StringIO,
        ) as mock_stdout, patch(
            "sys.stderr",
            new_callable=StringIO,
        ):
            main([])
        # Should print help when no subcommand provided
        output = mock_stdout.getvalue()
        self.assertIn("usage:", output)

    def test_main_list_command(self):
        """Test main function with list command."""
        with patch(
            "sys.stdout",
            new_callable=StringIO,
        ), patch(
            "sys.stderr",
            new_callable=StringIO,
        ):
            main(["list", self.temp_file.name])

    def test_main_dump_json(self):
        """Test main function with dump JSON command."""
        with patch(
            "sys.stdout",
            new_callable=StringIO,
        ), patch(
            "sys.stderr",
            new_callable=StringIO,
        ):
            main(["dump", self.temp_file.name, "--format", "json"])

    def test_main_dump_csv(self):
        """Test main function with dump CSV command."""
        with patch(
            "sys.stdout",
            new_callable=StringIO,
        ), patch(
            "sys.stderr",
            new_callable=StringIO,
        ):
            main(
                [
                    "dump",
                    self.temp_file.name,
                    "timestamp",
                    "value",
                    "--format",
                    "csv",
                ]
            )

    def test_main_serve_command(self):
        """Test main function with serve command."""
        cli_main_module = sys.modules["mpacklog.cli.main"]
        with patch.object(
            cli_main_module,
            "LogServer",
        ) as mock_server, patch(
            "logging.getLogger",
        ):
            mock_server_instance = MagicMock()
            mock_server.return_value = mock_server_instance

            main(["serve", "/path/to/logs", "--port", "8080"])

            mock_server.assert_called_once_with("/path/to/logs", 8080)
            mock_server_instance.run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
