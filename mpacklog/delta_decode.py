#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Inria

"""Read dictionaries from delta-compressed log files."""

from typing import Generator

import msgpack


def delta_decode(
    path: str,
    chunk_size: int = 100_000,
) -> Generator[dict, None, None]:
    """Read dictionaries from a delta-compressed log file.

    Args:
        path: Path to the delta-compressed log file to read.
        chunk_size: Optional, number of bytes to read per internal loop cycle.

    Returns:
        Generator to each cumulative dictionary from the log file, in sequence.
        Each yielded dictionary is cumulatively updated with all previous
        deltas.
    """
    cumulative_dict = {}
    with open(path, "rb") as file:
        unpacker = msgpack.Unpacker(raw=False)
        while True:
            data = file.read(chunk_size)
            if not data:  # end of file
                break
            unpacker.feed(data)
            for unpacked in unpacker:
                cumulative_dict.update(unpacked)
                yield cumulative_dict
