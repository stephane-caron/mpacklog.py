#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2022 Stéphane Caron

"""Main command line interface function."""

import argparse
import logging
import time

import msgpack

from mpacklog.delta_decode import delta_decode
from mpacklog.log_server import LogServer

from .csv_printer import CSVPrinter
from .field_printer import FieldPrinter
from .json_printer import JSONPrinter
from .printer import Printer


def get_argument_parser() -> argparse.ArgumentParser:
    """Parser for command-line arguments.

    Returns:
        Command-line argument parser.
    """
    main_parser = argparse.ArgumentParser(
        description="Manipulate MessagePack log files"
    )
    subparsers = main_parser.add_subparsers(title="subcommands", dest="subcmd")

    # mpacklog dump -----------------------------------------------------------
    dump_parser = subparsers.add_parser(
        "dump",
        help="Dump log file as JSON Lines to the standard output",
    )
    dump_parser.add_argument(
        "logfile", metavar="logfile", help="log file to open"
    )
    dump_parser.add_argument("fields", nargs="*", help="fields to plot")
    dump_parser.add_argument(
        "--format",
        choices=["csv", "json", "python"],
        default="json",
        help="output format (CSV, JSON Lines or Python script)",
    )
    dump_parser.add_argument(
        "-f",
        "--follow",
        action="store_true",
        help="keep file open and follow, as in `tail -f`",
    )
    dump_parser.add_argument(
        "--output-dir",
        metavar="output_dir",
        help="Output directory to write data and Python script to",
    )

    # mpacklog list -----------------------------------------------------------
    list_parser = subparsers.add_parser(
        "list",
        help="List all available fields encountered in log file",
    )
    list_parser.add_argument(
        "logfile", metavar="logfile", help="log file to open"
    )

    # mpacklog serve ----------------------------------------------------------
    serve_parser = subparsers.add_parser(
        "serve",
        help="Serve most recent values from log file",
    )
    serve_parser.add_argument(
        "log_path",
        help="path to a log directory (open most recent log) or a log file",
        type=str,
    )
    serve_parser.add_argument(
        "--port",
        "-p",
        help="port to listen to",
        type=int,
        default=4747,
    )

    # mpacklog delta_decode -----------------------------------------------
    delta_decode_parser = subparsers.add_parser(
        "delta_decode",
        help="Decode delta-encoded log file to a regular log file",
    )
    delta_decode_parser.add_argument(
        "input_file",
        metavar="input_file",
        help="delta-encoded log file to decode",
    )
    delta_decode_parser.add_argument(
        "output_file",
        metavar="output_file",
        help="output file for decoded log",
    )

    return main_parser


def decode_delta_log(input_file: str, output_file: str) -> None:
    """Decode delta-encoded log file to a regular log file.

    Args:
        input_file: Path to delta-encoded input log file.
        output_file: Path to output file for decoded log.
    """
    with open(output_file, "wb") as out_file:
        packer = msgpack.Packer()
        for cumulative_dict in delta_decode(input_file):
            packed_data = packer.pack(cumulative_dict)
            out_file.write(packed_data)


def dump_log(logfile: str, printer: Printer, follow: bool = False) -> None:
    """Dump log file.

    Args:
        logfile: Path to input log file.
        printer: Printer class to process unpacked messages.
        follow (optional): Keep file open and wait for updates?
    """
    with open(logfile, "rb") as filehandle:
        unpacker = msgpack.Unpacker(raw=False)
        while True:
            data = filehandle.read(4096)
            if not data:  # end of file
                if follow:
                    time.sleep(0.001)
                    continue
                break
            unpacker.feed(data)
            try:
                for unpacked in unpacker:
                    printer.process(unpacked)
            except BrokenPipeError:  # handle e.g. piping to `head`
                break


def main(argv=None) -> None:
    """Main function for the `mpacklog` command line.

    Args:
        argv: Command-line arguments.
    """
    parser = get_argument_parser()
    args = parser.parse_args(argv)
    if args.subcmd == "list":
        printer: Printer = FieldPrinter()
        dump_log(args.logfile, printer)
    elif args.subcmd == "dump":
        if args.format == "csv":
            printer = CSVPrinter(args.fields)
        elif args.format == "json":
            printer = JSONPrinter(args.fields)
        dump_log(args.logfile, printer, follow=args.follow)
    elif args.subcmd == "serve":
        logging.getLogger().setLevel(logging.INFO)
        server = LogServer(args.log_path, args.port)
        server.run()
    elif args.subcmd == "delta_decode":
        decode_delta_log(args.input_file, args.output_file)
    else:  # no subcommand
        parser.print_help()
