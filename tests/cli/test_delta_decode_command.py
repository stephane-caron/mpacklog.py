#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the delta_decode command-line interface."""

import os
import tempfile
import unittest

import msgpack

from mpacklog import SyncLogger
from mpacklog.cli.main import decode_delta_log, get_argument_parser, main


class TestDeltaDecodeCommand(unittest.TestCase):
    """Test delta_decode CLI command."""

    def test_delta_decode_subcommand_parsing(self):
        """Test delta_decode subcommand parsing."""
        parser = get_argument_parser()
        args = parser.parse_args(
            ["delta_decode", "input.mpack", "output.mpack"]
        )
        self.assertEqual(args.subcmd, "delta_decode")
        self.assertEqual(args.input_file, "input.mpack")
        self.assertEqual(args.output_file, "output.mpack")

    def test_decode_delta_log_function(self):
        """Test basic delta decoding functionality."""
        # Create delta-encoded input file
        input_file = tempfile.mktemp(suffix=".mpack")
        logger = SyncLogger(input_file)
        logger.put({"a": 1, "b": 2})
        logger.put({"b": 20, "c": 3})
        logger.write()

        # Create output file
        output_file = tempfile.mktemp(suffix=".mpack")

        try:
            # Decode the file
            decode_delta_log(input_file, output_file)

            # Verify the output
            with open(output_file, "rb") as f:
                unpacker = msgpack.Unpacker(raw=False)
                unpacker.feed(f.read())
                decoded_dicts = list(unpacker)

            self.assertEqual(len(decoded_dicts), 2)
            self.assertEqual(decoded_dicts[0], {"a": 1, "b": 2})
            self.assertEqual(decoded_dicts[1], {"a": 1, "b": 20, "c": 3})

        finally:
            if os.path.exists(input_file):
                os.unlink(input_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_main_delta_decode_command_integration(self):
        """Test main function with delta_decode command."""
        # Create delta-encoded input file
        delta_input = tempfile.mktemp(suffix=".mpack")
        logger = SyncLogger(delta_input)
        logger.put({"foo": 12, "something": "else"})
        logger.put({"foo": 42, "bar": "baz"})
        logger.write()

        # Create temporary output file
        output_file = tempfile.mktemp(suffix=".mpack")

        try:
            # Run delta_decode command
            main(["delta_decode", delta_input, output_file])

            # Verify the output file was created and contains expected data
            self.assertTrue(os.path.exists(output_file))

            # Read and verify the decoded content
            with open(output_file, "rb") as f:
                unpacker = msgpack.Unpacker(raw=False)
                unpacker.feed(f.read())
                decoded_dicts = list(unpacker)

            # Should have 2 cumulative dictionaries
            self.assertEqual(len(decoded_dicts), 2)
            self.assertEqual(
                decoded_dicts[0], {"foo": 12, "something": "else"}
            )
            self.assertEqual(
                decoded_dicts[1],
                {"foo": 42, "something": "else", "bar": "baz"},
            )

        finally:
            # Clean up
            if os.path.exists(delta_input):
                os.unlink(delta_input)
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_decode_delta_log_empty_input(self):
        """Test decoding empty delta file."""
        # Create empty input file
        input_file = tempfile.mktemp(suffix=".mpack")
        with open(input_file, "wb") as f:
            pass  # Create empty file

        output_file = tempfile.mktemp(suffix=".mpack")

        try:
            decode_delta_log(input_file, output_file)

            # Should create empty output file
            with open(output_file, "rb") as f:
                content = f.read()
                self.assertEqual(len(content), 0)

        finally:
            if os.path.exists(input_file):
                os.unlink(input_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_decode_delta_log_complex_data(self):
        """Test decoding delta file with complex nested data."""
        input_file = tempfile.mktemp(suffix=".mpack")
        logger = SyncLogger(input_file)
        logger.put(
            {
                "timestamp": 1.0,
                "values": {"x": 1, "y": 2},
                "metadata": {"source": "sensor1"},
            }
        )
        logger.put(
            {"timestamp": 2.0, "values": {"x": 10, "z": 3}, "status": "active"}
        )
        logger.put(
            {
                "values": {"y": 20},
                "metadata": {"source": "sensor2", "calibrated": True},
            }
        )
        logger.write()

        output_file = tempfile.mktemp(suffix=".mpack")

        try:
            decode_delta_log(input_file, output_file)

            with open(output_file, "rb") as f:
                unpacker = msgpack.Unpacker(raw=False)
                unpacker.feed(f.read())
                decoded_dicts = list(unpacker)

            self.assertEqual(len(decoded_dicts), 3)

            # First cumulative state
            expected_first = {
                "timestamp": 1.0,
                "values": {"x": 1, "y": 2},
                "metadata": {"source": "sensor1"},
            }
            self.assertEqual(decoded_dicts[0], expected_first)

            # Second cumulative state
            expected_second = {
                "timestamp": 2.0,
                "values": {"x": 10, "z": 3},
                "metadata": {"source": "sensor1"},
                "status": "active",
            }
            self.assertEqual(decoded_dicts[1], expected_second)

            # Third cumulative state
            expected_third = {
                "timestamp": 2.0,
                "values": {"y": 20},
                "metadata": {"source": "sensor2", "calibrated": True},
                "status": "active",
            }
            self.assertEqual(decoded_dicts[2], expected_third)

        finally:
            if os.path.exists(input_file):
                os.unlink(input_file)
            if os.path.exists(output_file):
                os.unlink(output_file)


if __name__ == "__main__":
    unittest.main()
