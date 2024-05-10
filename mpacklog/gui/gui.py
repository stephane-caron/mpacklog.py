#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2023 mjbots Robotic Systems, LLC.  info@mjbots.com
# Copyright 2024 Inria
#
# This file incorporates code from utils/gui/moteus_gui/tview.py
# (https://github.com/mjbots/moteus, 49c698a63f0ded22528ad7539cc2e27e41cd486d)

"""Interactively display and update values from an embedded device."""

import asyncio
import os
import sys

import moteus.reader as reader
import numpy
from PySide2 import QtUiTools
from qtpy import QtCore, QtWidgets
from stream_client import StreamClient

os.environ["QT_API"] = "pyside2"

import asyncqt  # noqa: E402
from plot_widget import PlotWidget  # noqa: E402

DEFAULT_RATE = 100
MAX_HISTORY_SIZE = 100
MAX_SEND = 61
POLL_TIMEOUT_S = 0.1
STARTUP_TIMEOUT_S = 0.5

FORMAT_ROLE = QtCore.Qt.UserRole + 1

FMT_STANDARD = 0
FMT_HEX = 1


class CommandError(RuntimeError):
    def __init__(self, cmd, err):
        super(CommandError, self).__init__(f'CommandError: "{cmd}" => "{err}"')


def _has_nonascii(data):
    return any([ord(x) > 127 for x in data])


def _get_data(value, name):
    fields = name.split(".")
    for field in fields:
        if isinstance(value, list):
            value = value[int(field)]
        else:
            value = getattr(value, field)
    return value


def _add_schema_item(parent, element, terminal_flags=None):
    # Cache our schema, so that we can use it for things like
    # generating better input options.
    parent.setData(1, QtCore.Qt.UserRole, element)

    if isinstance(element, reader.ObjectType):
        for field in element.fields:
            name = field.name

            item = QtWidgets.QTreeWidgetItem(parent)
            item.setText(0, name)

            _add_schema_item(
                item, field.type_class, terminal_flags=terminal_flags
            )
    else:
        if terminal_flags:
            parent.setFlags(terminal_flags)


def _set_tree_widget_data(item, struct, element, terminal_flags=None):
    if (
        isinstance(element, reader.ObjectType)
        or isinstance(element, reader.ArrayType)
        or isinstance(element, reader.FixedArrayType)
    ):
        if not isinstance(element, reader.ObjectType):
            for i in range(item.childCount(), len(struct)):
                subitem = QtWidgets.QTreeWidgetItem(item)
                subitem.setText(0, str(i))
                _add_schema_item(
                    subitem, element.type_class, terminal_flags=terminal_flags
                )
        for i in range(item.childCount()):
            child = item.child(i)
            if isinstance(struct, list):
                field = struct[i]
                child_element = element.type_class
            else:
                name = child.text(0)
                field = getattr(struct, name)
                child_element = element.fields[i].type_class
            _set_tree_widget_data(
                child, field, child_element, terminal_flags=terminal_flags
            )
    else:
        maybe_format = item.data(1, FORMAT_ROLE)
        text = None
        if maybe_format == FMT_HEX and type(struct) == int:
            text = f"{struct:x}"
        else:
            text = repr(struct)
        item.setText(1, text)


def _console_escape(value):
    if "\x00" in value:
        return value.replace("\x00", "*")
    return value


class RecordSignal(object):
    def __init__(self):
        self._index = 0
        self._callbacks = {}

    def connect(self, handler):
        result = self._index
        self._index += 1
        self._callbacks[result] = handler

        class Connection(object):
            def __init__(self, parent, index):
                self.parent = parent
                self.index = index

            def remove(self):
                del self.parent._callbacks[self.index]

        return Connection(self, result)

    def update(self, value):
        for handler in self._callbacks.values():
            handler(value)
        return len(self._callbacks) != 0


class SizedTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        QtWidgets.QTreeWidget.__init__(self, parent)
        self.setColumnCount(2)
        self.headerItem().setText(0, "Name")
        self.headerItem().setText(1, "Value")

    def sizeHint(self):
        return QtCore.QSize(350, 500)


class Record:
    def __init__(self, archive):
        self.archive = archive
        self.tree_item = None
        self.signals = {}
        self.history = []

    def get_signal(self, name):
        if name not in self.signals:
            self.signals[name] = RecordSignal()

        return self.signals[name]

    def update(self, struct):
        count = 0
        self.history.append(struct)
        if len(self.history) > MAX_HISTORY_SIZE:
            self.history = self.history[1:]

        for key, signal in self.signals.items():
            if key.startswith("__STDDEV_"):
                remaining = key.split("__STDDEV_")[1]
                values = [_get_data(x, remaining) for x in self.history]
                value = numpy.std(values)
            elif key.startswith("__MEAN_"):
                remaining = key.split("__MEAN_")[1]
                values = [_get_data(x, remaining) for x in self.history]
                value = numpy.mean(values)
            else:
                value = _get_data(struct, key)
            if signal.update(value):
                count += 1
        return count != 0


class NoEditDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        QtWidgets.QStyledItemDelegate.__init__(self, parent=parent)

    def createEditor(self, parent, option, index):
        return None


class EditDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        QtWidgets.QStyledItemDelegate.__init__(self, parent=parent)

    def createEditor(self, parent, option, index):
        maybe_schema = index.data(QtCore.Qt.UserRole)

        if maybe_schema is not None and (
            isinstance(maybe_schema, reader.EnumType)
            or isinstance(maybe_schema, reader.BooleanType)
        ):
            editor = QtWidgets.QComboBox(parent)

            if isinstance(maybe_schema, reader.EnumType):
                options = list(maybe_schema.enum_class)
                options_text = [repr(x) for x in options]
                editor.setEditable(True)
                editor.lineEdit().editingFinished.connect(
                    self.commitAndCloseEditor
                )
            elif isinstance(maybe_schema, reader.BooleanType):
                options_text = ["False", "True"]
                editor.activated.connect(self.commitAndCloseEditor)

            editor.insertItems(0, options_text)

            return editor
        else:
            return super(EditDelegate, self).createEditor(
                parent, option, index
            )

    def commitAndCloseEditor(self):
        editor = self.sender()

        self.commitData.emit(editor)
        self.closeEditor.emit(editor)


def _get_item_name(item):
    name = item.text(0)
    while item.parent() and item.parent().parent():
        name = item.parent().text(0) + "." + name
        item = item.parent()

    return name


def _get_item_root(item):
    while item.parent().parent():
        item = item.parent()
    return item.text(0)


class MpacklogMainWindow:
    """Main application window.

    Attributes:
        stream_client: Client to read streaming data from.
    """

    stream_client: StreamClient

    def __init__(self, host: str, port: int, parent=None):
        stream_client = StreamClient(host, port)
        self.default_rate = 100
        self.user_task = None

        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        uifilename = os.path.join(current_script_dir, "mpacklog.ui")

        loader = QtUiTools.QUiLoader()
        uifile = QtCore.QFile(uifilename)
        uifile.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(uifile, parent)
        uifile.close()

        self.ui.telemetryTreeWidget = SizedTreeWidget()
        self.ui.telemetryDock.setWidget(self.ui.telemetryTreeWidget)
        self.ui.telemetryTreeWidget.itemExpanded.connect(
            self._handle_tree_expanded
        )
        self.ui.telemetryTreeWidget.itemCollapsed.connect(
            self._handle_tree_collapsed
        )
        self.ui.telemetryTreeWidget.setContextMenuPolicy(
            QtCore.Qt.CustomContextMenu
        )
        self.ui.telemetryTreeWidget.customContextMenuRequested.connect(
            self._handle_telemetry_context_menu
        )

        self.ui.plotItemRemoveButton.clicked.connect(
            self._handle_plot_item_remove
        )

        # self.ui.tabifyDockWidget(self.ui.telemetryDock)

        layout = QtWidgets.QVBoxLayout(self.ui.plotHolderWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.ui.plotHolderWidget.setLayout(layout)
        self.ui.plotWidget = PlotWidget(self.ui.plotHolderWidget)
        layout.addWidget(self.ui.plotWidget)

        def update_plotwidget(value):
            self.ui.plotWidget.history_s = value

        self.ui.historySpin.valueChanged.connect(update_plotwidget)

        QtCore.QTimer.singleShot(0, self._handle_startup)
        self.stream_client = stream_client

    def show(self):
        self.ui.show()

    def _handle_startup(self):
        asyncio.create_task(self._run_transport())
        self.ui.telemetryTreeWidget.clear()

    async def _run_transport(self):
        any_data_read = False
        while True:
            # We only sleep if no devices had anything to report the last
            # cycle.
            if not any_data_read:
                await asyncio.sleep(0.01)

            any_data_read = await self._run_transport_iteration()

    async def _run_transport_iteration(self):
        any_data_read = False
        return any_data_read

    def _handle_tree_expanded(self, item):
        self.ui.telemetryTreeWidget.resizeColumnToContents(0)
        user_data = item.data(0, QtCore.Qt.UserRole)
        if user_data:
            user_data.expand()

    def _handle_tree_collapsed(self, item):
        user_data = item.data(0, QtCore.Qt.UserRole)
        if user_data:
            user_data.collapse()

    def _handle_telemetry_context_menu(self, pos):
        item = self.ui.telemetryTreeWidget.itemAt(pos)
        if item.childCount() > 0:
            return

        menu = QtWidgets.QMenu(self.ui)
        left_action = menu.addAction("Plot Left")
        right_action = menu.addAction("Plot Right")
        left_std_action = menu.addAction("Plot StdDev Left")
        right_std_action = menu.addAction("Plot StdDev Right")
        left_mean_action = menu.addAction("Plot Mean Left")
        right_mean_action = menu.addAction("Plot Mean Right")

        plot_actions = [
            left_action,
            right_action,
            left_std_action,
            right_std_action,
            left_mean_action,
            right_mean_action,
        ]

        right_actions = [right_action, right_std_action, right_mean_action]
        std_actions = [left_std_action, right_std_action]
        mean_actions = [left_mean_action, right_mean_action]

        menu.addSeparator()
        copy_name = menu.addAction("Copy Name")
        copy_value = menu.addAction("Copy Value")

        menu.addSeparator()
        fmt_standard_action = menu.addAction("Standard Format")
        fmt_hex_action = menu.addAction("Hex Format")

        requested = menu.exec_(self.ui.telemetryTreeWidget.mapToGlobal(pos))

        if requested in plot_actions:
            top = item
            while top.parent().parent():
                top = top.parent()

            schema = top.data(0, QtCore.Qt.UserRole)
            record = schema.record

            name = _get_item_name(item)

            leaf = name.split(".", 1)[1]
            axis = 0
            if requested in right_actions:
                axis = 1

            if requested in std_actions:
                leaf = "__STDDEV_" + leaf
                name = "stddev " + name

            if requested in mean_actions:
                leaf = "__MEAN_" + leaf
                name = "mean " + name

            plot_item = self.ui.plotWidget.add_plot(
                name, record.get_signal(leaf), axis
            )
            self.ui.plotItemCombo.addItem(name, plot_item)
        elif requested == copy_name:
            QtWidgets.QApplication.clipboard().setText(item.text(0))
        elif requested == copy_value:
            QtWidgets.QApplication.clipboard().setText(item.text(1))
        elif requested == fmt_standard_action:
            item.setData(1, FORMAT_ROLE, FMT_STANDARD)
        elif requested == fmt_hex_action:
            item.setData(1, FORMAT_ROLE, FMT_HEX)
        else:  # the user cancelled
            pass

    def _handle_plot_item_remove(self):
        index = self.ui.plotItemCombo.currentIndex()
        if index < 0:
            return
        item = self.ui.plotItemCombo.itemData(index)
        self.ui.plotWidget.remove_plot(item)
        self.ui.plotItemCombo.removeItem(index)


def main():
    app = QtWidgets.QApplication(sys.argv)
    loop = asyncqt.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # To work around https://bugreports.qt.io/browse/PYSIDE-88
    app.aboutToQuit.connect(lambda: os._exit(0))

    window = MpacklogMainWindow("localhost", 4747)
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()