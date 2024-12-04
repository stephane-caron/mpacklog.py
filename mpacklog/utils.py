#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2022 Stéphane Caron

"""Utility functions."""

import glob
import logging
import os


def find_log_file(path: str) -> str:
    """Find the most recent log file to open in a path.

    Args:
        path: Path to a directory or a specific log file.
    """
    if os.path.exists(path):
        if os.path.isfile(path):
            return path
    mpack_files = glob.glob(os.path.join(path, "*.mpack"))
    log_file = max(mpack_files, key=os.path.getmtime)
    logging.info(
        "Opening the most recent log in %s: %s",
        path,
        os.path.basename(log_file),
    )
    return log_file
