# Changelog

## Unreleased

## [4.0.1] - 2024-12-04

### Added

- docs: Section on reading logs
- Support Python 3.12
- Unit test for `find_log_file`
- Unit test for `read_log`

### Changed

- Bump development status to stable
- docs: Structure of the documentation

### Fixed

- docs: Readme links to the documentation
- Correct OSI classifier of project license

## [4.0.0] - 2024-06-07

### Added

- AsyncLogger: flush function to empty the message queue to file
- CLI: ``mpacklog serve`` sub-command
- Example showing how to extend an existing log with new fields
- New ``read_log`` function to get dictionaries from an input log
- Server class to stream data from a MessagePack log

### Changed

- CICD: Update ruff to 0.4.3
- Use SPDX license identifiers in all source files

### Fixed

- AsyncLogger: Wait for logger to stop properly

## [3.1.0] - 2023-09-29

### Added

- Complete project documentation

### Changed

- Move C++ version to ``mpacklog.cpp``
- Switch docstring style from Doxygen to Google convention

### Removed

- Unused script printer from CLI
- Unused `finish` function from CLI printers

## [3.0.0] - 2023-06-06

### Added

- Synchronous ``SyncLogger`` class

### Changed

- CI: Update Bazelisk script
- Rename ``Logger`` to ``AsyncLogger``
- Remove unused ``mypy_integration``

## [2.1.0] - 2023-04-26

### Changed

- Make code compatible with macOS (thanks to @boragokbakan)

## [2.0.0] - 2022-09-01

### Added

- Dump log to CSV from the command line
- Dump log to JSON from the command line
- Dump log to Python script from the command line
- List log fields from the command line
- Python `Logger` implementation
- `mpacklog` command-line tool
- Unit tests for Python API

## [1.0.0] - 2022-08-17

First release of the project.

[unreleased]: https://github.com/stephane-caron/mpacklog.py/compare/v4.0.1...HEAD
[4.0.1]: https://github.com/stephane-caron/mpacklog.py/compare/v4.0.0...v4.0.1
[4.0.0]: https://github.com/stephane-caron/mpacklog.py/compare/v3.1.0...v4.0.0
[3.1.0]: https://github.com/stephane-caron/mpacklog.py/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/stephane-caron/mpacklog.py/compare/v2.1.0...v3.0.0
[2.1.0]: https://github.com/stephane-caron/mpacklog.py/compare/v2.0.1...v2.1.0
[2.0.0]: https://github.com/stephane-caron/mpacklog.py/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/stephane-caron/mpacklog.py/releases/tag/v1.0.0
