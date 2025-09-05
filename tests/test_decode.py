#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 Inria

"""Test decoding logs to Python dictionaries."""

import tempfile
import unittest

from mpacklog import SyncLogger, decode


class TestDecode(unittest.TestCase):
    def test_decode(self):
        tmp_file = tempfile.mktemp(suffix=".mpack")
        logger = SyncLogger(tmp_file)
        logger.put({"foo": 12, "something": "else"})
        logger.put({"foo": 42, "bar": "baz"})
        logger.write()

        read_dicts = list(decode(tmp_file))
        self.assertEqual(len(read_dicts), 2)
        self.assertEqual(read_dicts[0], {"foo": 12, "something": "else"})
        self.assertEqual(read_dicts[1], {"foo": 42, "bar": "baz"})
