#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 Inria

import math
import os

from mpacklog import SyncLogger, read_log

CURDIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = f"{CURDIR}/data/upkie.mpack"
OUTPUT_PATH = f"{CURDIR}/data/upkie_extended.mpack"


def process_input(unpacked: dict) -> dict:
    """Adding any processing of the input dictionary series here.

    Args:
        unpacked: Input dictionary.

    Returns:
        Output dictionary.
    """
    state = unpacked["spine"]["state"]
    left_wheel = unpacked["observation"]["servo"]["left_wheel"]
    output = unpacked.copy()
    output["extra"] = {
        "foo": state["cycle_beginning"] + state["cycle_end"],
        "bar": math.isnan(left_wheel["q_current"]),
    }
    return output


if __name__ == "__main__":
    logger = SyncLogger(OUTPUT_PATH)
    for unpacked in read_log(INPUT_PATH):
        logger.put(process_input(unpacked))
    logger.write()
    print(f'Extended log written to "{OUTPUT_PATH}"')
