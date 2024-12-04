#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 Inria

"""Test utility functions."""

import tempfile
import os
import unittest

from mpacklog import SyncLogger
from mpacklog.utils import find_log_file


class TestUtils(unittest.TestCase):
    def test_find_log_file(self):
        tmp_files = []
        for _ in range(3):
            tmp_file = tempfile.mktemp(suffix=".mpack")
            logger = SyncLogger(tmp_file)
            logger.put({"foo": 12, "something": "else"})
            logger.put({"foo": 42, "bar": "foo"})
            logger.write()
            tmp_files.append(tmp_file)
        log_file = find_log_file(tempfile.gettempdir())
        latest_tmp_file = max(tmp_files, key=os.path.getmtime)
        self.assertEqual(log_file, latest_tmp_file)
