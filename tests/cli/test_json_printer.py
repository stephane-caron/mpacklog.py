#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the JSON printer."""

import unittest
from io import StringIO
from unittest.mock import patch

from mpacklog.cli.json_printer import JSONPrinter


class TestJSONPrinter(unittest.TestCase):
    """Test JSONPrinter class - additional tests for better coverage."""

    def test_initialization_with_empty_fields(self):
        """Test JSON printer with empty fields list."""
        printer = JSONPrinter([])
        self.assertEqual(printer.fields, [])

    def test_initialization_with_none_fields(self):
        """Test JSON printer with None fields."""
        printer = JSONPrinter(None)
        self.assertIsNone(printer.fields)

    def test_process_with_field_filtering(self):
        """Test processing with specific field filtering."""
        printer = JSONPrinter(["field1", "nested/value"])
        data = {
            "field1": "keep",
            "field2": "ignore",
            "nested": {"value": "keep", "ignore": "ignore"},
        }

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer.process(data)

        output = mock_stdout.getvalue().strip()
        # Should contain filtered fields
        # Note that `set_from_keys` flattens the structure
        self.assertIn('"field1": "keep"', output)
        self.assertIn('"nested": "keep"', output)
        # Should not contain ignored field
        self.assertNotIn("ignore", output)

    def test_process_all_fields(self):
        """Test processing without field filtering."""
        printer = JSONPrinter(None)
        data = {"field1": "value1", "field2": "value2"}

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer.process(data)

        output = mock_stdout.getvalue().strip()
        self.assertIn('"field1": "value1"', output)
        self.assertIn('"field2": "value2"', output)

    def test_process_nonexistent_field(self):
        """Test processing with nonexistent field shows error message."""
        printer = JSONPrinter(["nonexistent/field"])
        data = {"existing": "value"}

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer.process(data)

        output = mock_stdout.getvalue()
        self.assertIn("Field", output)
        self.assertIn("not found", output)

    def test_process_complex_nested_data(self):
        """Test processing complex nested data structures."""
        printer = JSONPrinter(["complex/nested/deep"])
        data = {
            "complex": {"nested": {"deep": "target_value", "other": "ignored"}}
        }

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            printer.process(data)

        output = mock_stdout.getvalue().strip()
        # Due to set_from_keys behavior, the nested structure is flattened
        self.assertIn('"complex": "target_value"', output)
        self.assertNotIn("ignored", output)


if __name__ == "__main__":
    unittest.main()
