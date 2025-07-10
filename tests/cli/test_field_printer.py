#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the field printer."""

import unittest
from io import StringIO
from unittest.mock import patch

from mpacklog.cli.field_printer import FieldPrinter


class TestFieldPrinter(unittest.TestCase):
    """Test FieldPrinter class."""

    def test_initialization(self):
        """Test field printer initialization."""
        printer = FieldPrinter()
        self.assertEqual(printer.fields, set())
        self.assertEqual(printer.observation, {})

    def test_process_simple_dict(self):
        """Test processing a simple dictionary."""
        printer = FieldPrinter()
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer.process({"key1": "value1", "key2": "value2"})

        output = mock_stdout.getvalue()
        self.assertIn("- key1", output)
        self.assertIn("- key2", output)
        self.assertEqual(printer.fields, {"key1", "key2"})

    def test_process_nested_dict(self):
        """Test processing a nested dictionary."""
        printer = FieldPrinter()
        data = {"level1": {"level2": "value"}, "simple": "test"}

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer.process(data)

        output = mock_stdout.getvalue()
        self.assertIn("- level1/level2", output)
        self.assertIn("- simple", output)
        self.assertEqual(printer.fields, {"level1/level2", "simple"})

    def test_process_incremental_fields(self):
        """Test processing multiple dictionaries with incremental fields."""
        printer = FieldPrinter()

        # First dictionary
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer.process({"field1": "value1"})
        output1 = mock_stdout.getvalue()

        # Second dictionary with new field
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer.process({"field1": "value1", "field2": "value2"})
        output2 = mock_stdout.getvalue()

        self.assertIn("- field1", output1)
        self.assertIn("- field2", output2)
        self.assertNotIn(
            "- field1", output2
        )  # Shouldn't print existing fields
        self.assertEqual(printer.fields, {"field1", "field2"})

    def test_process_no_new_fields(self):
        """Test processing dictionary with no new fields."""
        printer = FieldPrinter()
        printer.fields = {"existing"}

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer.process({"existing": "value"})

        output = mock_stdout.getvalue()
        self.assertEqual(output, "")  # No output for existing fields

    def test_observation_update(self):
        """Test that observation is updated with new data."""
        printer = FieldPrinter()
        data = {"key": "value"}
        with patch("sys.stdout", new_callable=StringIO):
            printer.process(data)
        self.assertEqual(printer.observation["key"], "value")


if __name__ == "__main__":
    unittest.main()
