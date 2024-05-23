# mpacklog.py

[![Build](https://img.shields.io/github/actions/workflow/status/upkie/mpacklog.py/ci.yml?branch=main)](https://github.com/upkie/mpacklog.py/actions)
[![Coverage](https://coveralls.io/repos/github/upkie/mpacklog.py/badge.svg?branch=main)](https://coveralls.io/github/upkie/mpacklog.py?branch=main)
[![Conda version](https://anaconda.org/conda-forge/mpacklog/badges/version.svg)](https://anaconda.org/conda-forge/mpacklog)
[![PyPI version](https://img.shields.io/pypi/v/mpacklog)](https://pypi.org/project/mpacklog/)

Stream dictionaries to files or over the network using MessagePack in Python.

## Installation

### From conda-forge

```console
conda install -c conda-forge mpacklog
```

### From PyPI

```console
pip install mpacklog
```

## Usage

#### Asynchronous API

Add messages to the log using the [`put`](https://scaron.info/doc/mpacklog/classmpacklog_1_1mpacklog_1_1python_1_1logger_1_1Logger.html#aa0f928ac07280acd132627d8545a7e18) function, have them written to file in the separate [`write`](https://scaron.info/doc/mpacklog/classmpacklog_1_1mpacklog_1_1python_1_1logger_1_1Logger.html#acbea9c05c465423efc3f38a25ed699d2) coroutine.

```python
import asyncio
import mpacklog

async def main():
    logger = mpacklog.AsyncLogger("output.mpack")
    await asyncio.gather(main_loop(logger), logger.write())

async def main_loop(logger):
    for bar in range(1000):
        await asyncio.sleep(1e-3)
        await logger.put({"foo": bar, "something": "else"})
    await logger.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

#### Synchronous API

The synchronous API is similar to the asynchronous API, except it doesn't provide a ``stop`` method and the ``put`` and ``write`` methods are blocking.

```python
import mpacklog

logger = mpacklog.SyncLogger("output.mpack")

for bar in range(1000):
    logger.put({"foo": bar, "something": "else"})

# Flush all messages to the file
logger.write()
```

## Command-line

The ``mpacklog`` utility provides commands to manipulate ``.mpack`` files.

### ``dump``

The ``dump`` command writes down a log file to [newline-delimited JSON](https://jsonlines.org):

```console
mpacklog dump my_log.mpack
```

## See also

There are two fantastic tools to manipulate newline-delimited JSON logs from the command line:

* [`jq`](https://github.com/stedolan/jq): manipulate JSON series to add, remove or extend fields
* [`rq`](https://github.com/dflemstr/rq): transform from/to MessagePack, JSON, YAML, TOML, ...

For instance, ``mpacklog dump`` is equivalent to ``rq -mJ < my_log.mpack``.
