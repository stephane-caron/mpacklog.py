#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2022 Stéphane Caron

"""Test the serialization function."""

import unittest

import numpy as np

from mpacklog.serialize import serialize


class FooSerializer:
    def serialize(self):
        return {"foo": "bar"}


class MockPinocchioSE3:
    def __init__(self, array: np.ndarray):
        self.np = array


class TestSerialize(unittest.TestCase):
    def test_serialize(self):
        foo = FooSerializer()
        x = np.array([1, 2, 3])
        some_int = 42
        self.assertEqual(serialize(x), list(x))
        self.assertEqual(serialize(MockPinocchioSE3(x)), list(x))
        self.assertEqual(serialize(foo), {"foo": "bar"})
        self.assertEqual(serialize(some_int), some_int)  # returned as-is
