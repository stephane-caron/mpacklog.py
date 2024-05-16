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
from loop_rate_limiters import AsyncRateLimiter

from mpacklog import AsyncLogger
from mpacklog.cli.server import Server


class TestServer(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()

        log_file = tempfile.mktemp(suffix=".mpack")
        self.logger = AsyncLogger(log_file)
        await self.logger.flush()
        asyncio.create_task(self.logger.write())

        self.server = Server(log_file, 4949)
        asyncio.create_task(self.server.run_async())
        asyncio.create_task(self.log_ten_foos())

    async def log_ten_foos(self):
        rate = AsyncRateLimiter(frequency=1000.0, name="log", warn=False)
        for foo in range(10):
            await self.logger.put({"foo": foo})
            await self.logger.write()
            await rate.sleep()

    async def test_get(self):
        unpacker = msgpack.Unpacker(raw=False)
        loop = asyncio.get_event_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect(("localhost", 4949))
        sock.setblocking(False)

        for trial in range(10):
            request = "get".encode("utf-8")
            await loop.sock_sendall(sock, request)
            reply = None
            data = await loop.sock_recv(sock, 4096)
            if not data:
                return None
            unpacker.feed(data)
            for unpacked in unpacker:
                reply = unpacked
            if reply:
                break

        sock.close()
        self.assertTrue("foo" in reply)
        self.assertIsInstance(reply["foo"], int)
        self.assertGreaterEqual(reply["foo"], 0)
        self.assertLess(reply["foo"], 10)
