#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 Inria

"""Server to stream from MessagePack dictionary logs."""

import asyncio
import logging
import socket

import aiofiles
import msgpack
from loop_rate_limiters import AsyncRateLimiter

from mpacklog.serialize import serialize
from mpacklog.utils import find_log_file


class LogServer:
    """Server to stream from MessagePack dictionary logs.

    Attributes:
        last_log: Last logged dictionary.
        log_path: Path to a log file, or a directory containing log files.
        port: Port number to listen to.
    """

    last_log: dict
    log_path: str
    port: int

    def __init__(
        self,
        log_path: str,
        port: int,
        frequency: float = 2000.0,
        read_from_beginning: bool = False,
    ):
        """Prepare a new server.

        Args:
            log_path: Path to a log file, or a directory containing log files.
            port: Port number to listen to.
            frequency: Rate limiting frequency in Hz for the two internal
                (unpack and serve) loops.
            read_from_beginning: If True, read the whole log file from its
                beginning. Otherwise (default), start reading from end of file.
        """
        self.__frequency = frequency
        self.__keep_going = True
        self.__read_from_beginning = read_from_beginning
        self.__stopped = 0
        self.last_log = {}
        self.log_path = log_path
        self.port = port

    def run(self) -> None:
        """Run the server using asyncio."""
        asyncio.run(self.run_async())

    async def run_async(self) -> None:
        """Start the two server coroutines."""
        await asyncio.gather(self.unpack(), self.listen())

    async def stop(self):
        """Stop the two server coroutines."""
        loop = asyncio.get_event_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost", self.port))
        sock.setblocking(False)
        self.__keep_going = False  # stop accepting new sockets
        await loop.sock_sendall(sock, "stop".encode("utf-8"))
        while self.__stopped < 2:
            await asyncio.sleep(0.01)
        sock.close()

    async def unpack(self):
        """Unpack latest data from log file."""
        log_file = find_log_file(self.log_path)
        rate = AsyncRateLimiter(
            frequency=self.__frequency,
            name="unpack",
            warn=False,
        )
        async with aiofiles.open(log_file, "rb") as file:
            await file.seek(0, 0 if self.__read_from_beginning else 2)
            unpacker = msgpack.Unpacker(raw=False)
            while self.__keep_going:
                data = await file.read(4096)
                if not data:  # end of file
                    await rate.sleep()
                    continue
                unpacker.feed(data)
                try:
                    for unpacked in unpacker:
                        if not isinstance(unpacked, dict):
                            raise ValueError(f"{unpacked=} not a dictionary")
                        self.last_log = unpacked
                except BrokenPipeError:  # handle e.g. piping to `head`
                    break
                await rate.sleep()

    async def serve(self, client, address) -> None:
        """Server a client connection.

        Args:
            client: Socket of connection to client.
            address: IP address and port of the connection.
        """
        loop = asyncio.get_event_loop()
        request: str = "start"
        packer = msgpack.Packer(default=serialize, use_bin_type=True)
        logging.info("New connection from %s", address)
        rate = AsyncRateLimiter(
            frequency=self.__frequency,
            name="serve",
            warn=False,
        )
        try:
            while self.__keep_going:
                data = await loop.sock_recv(client, 4096)
                if not data:
                    break
                try:
                    request = data.decode("utf-8").strip()
                except UnicodeDecodeError as exn:
                    logging.warning(str(exn))
                    continue
                if request == "get":
                    reply = packer.pack(self.last_log)
                    await loop.sock_sendall(client, reply)
                elif request == "stop":
                    self.__keep_going = False
                await rate.sleep()
        except BrokenPipeError:
            logging.info("Connection closed by %s", address)
        logging.info("Closing connection with %s", address)
        client.close()
        self.__stopped += 1

    async def listen(self):
        """Listen to clients connecting on a given port."""
        loop = asyncio.get_event_loop()
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", self.port))
        server_socket.listen(8)
        server_socket.setblocking(False)  # required by loop.sock_accept
        while self.__keep_going:
            client_socket, address = await loop.sock_accept(server_socket)
            loop.create_task(self.serve(client_socket, address))
        server_socket.close()
        self.__stopped += 1
