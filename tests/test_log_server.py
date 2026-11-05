#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2022 Stéphane Caron

"""Test the server."""

import asyncio
import socket
import tempfile
import unittest

import msgpack

from mpacklog import AsyncLogger, LogServer


class TestLogServer(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()

        log_file = tempfile.mktemp(suffix=".mpack")
        self.logger = AsyncLogger(log_file)
        await self.logger.flush()
        asyncio.create_task(self.logger.write())

        self.server = LogServer(log_file, 4949, read_from_beginning=True)
        asyncio.create_task(self.server.run_async())
        asyncio.create_task(self.log_ten_foos())

    async def asyncTearDown(self):
        await self.logger.stop()
        await self.server.stop()

    async def log_ten_foos(self):
        for foo in range(10):
            await self.logger.put({"foo": foo})
            await asyncio.sleep(0.001)

    async def test_get(self):
        unpacker = msgpack.Unpacker(raw=False)
        loop = asyncio.get_event_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect(("localhost", 4949))
        sock.setblocking(False)

        reply = None
        for trial in range(500):
            request = "get".encode("utf-8")
            await loop.sock_sendall(sock, request)
            data = await loop.sock_recv(sock, 4096)
            self.assertTrue(data, "connection closed by server")
            unpacker.feed(data)
            for unpacked in unpacker:
                reply = unpacked
            if reply:
                break
            await asyncio.sleep(0.01)

        sock.close()
        self.assertIsNotNone(reply)
        self.assertIn("foo", reply)
        self.assertIsInstance(reply["foo"], int)
        self.assertGreaterEqual(reply["foo"], 0)
        self.assertLess(reply["foo"], 10)
