#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0

"""Interactive example with a LogServer serving `./data/upkie.mpack`."""

import asyncio
from pathlib import Path

import msgpack

from mpacklog import LogServer


async def run_client(port: int):
    print("LogServer client session started.")
    print("Available commands:")
    print("  'get' - Request the latest log data")
    print("  'stop' - Stop the server")
    print("  'quit' - Exit client session")
    print("")

    while True:
        try:
            command = input("Enter command: ").strip().lower()

            if command == "quit":
                print("Exiting client session.")
                break
            elif command in ["get", "stop"]:
                # Create connection and send request
                reader, writer = await asyncio.open_connection(
                    "localhost", port
                )

                # Send command
                writer.write(command.encode("utf-8"))
                await writer.drain()

                if command == "get":
                    data = await reader.read(4096)
                    if data:
                        unpacker = msgpack.Unpacker(raw=False)
                        unpacker.feed(data)
                        for unpacked in unpacker:
                            print(f"Received dictionary: {unpacked}")
                            break
                    else:
                        print("No data received")
                elif command == "stop":
                    print("Stop command sent to server.")
                    writer.close()
                    await writer.wait_closed()
                    break

                writer.close()
                await writer.wait_closed()
            else:
                print("Unknown command. Use 'get', 'stop', or 'quit'.")

        except KeyboardInterrupt:
            print("\nExiting client session.")
            break


async def main_async(port: int = 1337):
    """Run both server and client concurrently."""
    data_path = Path(__file__).parent / "data" / "upkie.mpack"
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        return

    print(f"Starting LogServer on port {port} serving {data_path}")
    print("The server will serve the last dictionary from the log file.")
    print("")

    try:
        server = LogServer(
            data_path,
            port,
            frequency=500.0,
            read_from_beginning=True,
        )
        await asyncio.gather(server.run_async(), run_client(port))
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await server.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nShutting down...")
