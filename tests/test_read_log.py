#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 Inria

"""Test reading logs."""

import tempfile
import unittest

from mpacklog import SyncLogger, read_log


class TestReadLog(unittest.TestCase):
    def test_read_log(self):
        tmp_file = tempfile.mktemp(suffix=".mpack")
        logger = SyncLogger(tmp_file)
        logger.put({"foo": 12, "something": "else"})
        logger.put({"foo": 42, "bar": "foo"})
        logger.write()
        read_dicts = list(read_log(tmp_file))
        self.assertEqual(len(read_dicts), 2)
        self.assertEqual(read_dicts[-1]["foo"], 42)
