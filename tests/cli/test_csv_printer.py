#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the CSV printer."""

import unittest
from io import StringIO
from unittest.mock import patch

from mpacklog.cli.csv_printer import CSVPrinter


class TestCSVPrinter(unittest.TestCase):
    """Test CSVPrinter class."""

    def test_initialization_with_fields(self):
        """Test CSV printer initialization with fields."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer = CSVPrinter(["field1", "field2"])

        output = mock_stdout.getvalue()
        self.assertEqual(output.strip(), "time,field1,field2")
        self.assertEqual(printer.fields, ["time", "field1", "field2"])

    def test_initialization_with_time_field(self):
        """Test CSV printer initialization when time field already present."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer = CSVPrinter(["time", "field1"])

        output = mock_stdout.getvalue()
        self.assertEqual(output.strip(), "time,field1")
        self.assertEqual(printer.fields, ["time", "field1"])

    def test_initialization_empty_fields(self):
        """Test CSV printer initialization with empty fields raises error."""
        with self.assertRaises(ValueError) as cm:
            CSVPrinter([])
        self.assertIn("A list of fields is required", str(cm.exception))

    def test_process_simple_values(self):
        """Test processing simple values."""
        with patch("sys.stdout", new_callable=StringIO):
            printer = CSVPrinter(["field1", "field2"])

        data = {"time": 1.5, "field1": "value1", "field2": 42}
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer.process(data)

        output = mock_stdout.getvalue()
        self.assertEqual(output.strip(), "1.5,value1,42")

    def test_process_boolean_values(self):
        """Test processing boolean values."""
        with patch("sys.stdout", new_callable=StringIO):
            printer = CSVPrinter(["bool_true", "bool_false"])

        data = {"time": 1.0, "bool_true": True, "bool_false": False}
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer.process(data)

        output = mock_stdout.getvalue()
        self.assertEqual(output.strip(), "1.0,1,0")

    def test_process_missing_fields(self):
        """Test processing with missing fields uses default."""
        with patch("sys.stdout", new_callable=StringIO):
            printer = CSVPrinter(["existing", "missing"])

        data = {"time": 2.0, "existing": "present"}
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer.process(data)

        output = mock_stdout.getvalue()
        self.assertEqual(output.strip(), "2.0,present,0")

    def test_process_nested_fields(self):
        """Test processing nested field paths."""
        with patch("sys.stdout", new_callable=StringIO):
            printer = CSVPrinter(["nested/value"])

        data = {"time": 3.0, "nested": {"value": "nested_result"}}
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer.process(data)

        output = mock_stdout.getvalue()
        self.assertEqual(output.strip(), "3.0,nested_result")


if __name__ == "__main__":
    unittest.main()
