#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Inria

"""Test delta decoding logs to Python dictionaries."""

import tempfile
import unittest

from mpacklog import SyncLogger, delta_decode


class TestDeltaDecode(unittest.TestCase):
    def test_delta_decode(self):
        tmp_file = tempfile.mktemp(suffix=".mpack")
        logger = SyncLogger(tmp_file)
        logger.put({"foo": 12, "something": "else"})
        logger.put({"foo": 42, "bar": "baz"})
        logger.write()

        # Test step-by-step iteration to see cumulative building
        cumulative_states = []
        for state in delta_decode(tmp_file):
            cumulative_states.append(dict(state))

        self.assertEqual(len(cumulative_states), 2)
        self.assertEqual(
            cumulative_states[0], {"foo": 12, "something": "else"}
        )

        expected_cumulative = {"foo": 42, "something": "else", "bar": "baz"}
        self.assertEqual(cumulative_states[1], expected_cumulative)

    def test_delta_decode_multiple_updates(self):
        tmp_file = tempfile.mktemp(suffix=".mpack")
        logger = SyncLogger(tmp_file)
        logger.put({"a": 1, "b": 2})
        logger.put({"b": 20, "c": 3})
        logger.put({"a": 10, "d": 4})
        logger.write()

        cumulative_states = []
        for state in delta_decode(tmp_file):
            cumulative_states.append(dict(state))

        self.assertEqual(len(cumulative_states), 3)
        self.assertEqual(cumulative_states[0], {"a": 1, "b": 2})
        self.assertEqual(cumulative_states[1], {"a": 1, "b": 20, "c": 3})
        self.assertEqual(
            cumulative_states[2], {"a": 10, "b": 20, "c": 3, "d": 4}
        )
