#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 Inria

"""Read dictionaries in series from a log file."""

from typing import Generator

import msgpack


def read_log(
    path: str, chunk_size: int = 100_000
) -> Generator[dict, None, None]:
    """Read dictionaries in series from a log file.

    Args:
        path: Path to the log file to read.
        chunk_size: Optional, number of bytes to read per internal loop cycle.

    Returns:
        Generator to each dictionary from the log file, in sequence.
    """
    with open(path, "rb") as file:
        unpacker = msgpack.Unpacker(raw=False)
        while True:
            data = file.read(chunk_size)
            if not data:  # end of file
                break
            unpacker.feed(data)
            for unpacked in unpacker:
                yield unpacked
