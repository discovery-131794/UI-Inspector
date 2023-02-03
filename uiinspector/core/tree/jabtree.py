from __future__ import annotations
from collections import deque
from ctypes import byref
import re
from typing import Dict, List, Mapping, Tuple
from ...common.exceptions import ParseSelectorError
from ..pyjab import JDriver, JElement
from pyjab.accessibleinfo import AccessibleActions
from ..base import PropertyTableModel, UITreeItem
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QAbstractTableModel

class JABPropertyTableModel(PropertyTableModel):
    pass

class JABTreeItem(UITreeItem):
    def __init__(self, control: JElement = None, parent: JABTreeItem = None, display_name = None) -> None:
        if control is None:
            return
        self._depth = getattr(parent, "_depth", -1) + 1
        self._control = control
        self._role = control.role
        self._name = control.name
        self._desc = control.description
        self._display_name = self._role + " " + self._name.title()
        super().__init__(parent, [display_name or self._display_name])

        self._data = None
        self._model = None

    @property
    def control(self) -> JElement:
        return self._control

    @property
    def bounds(self) -> str:
        rect = self._control.bounds
        return f"X={rect['x']}, Y={rect['y']}, Width={rect['width']}, Height={rect['height']}"

    @property
    def properties(self):
        return [
                self._role, 
                self._name,
                self._desc,
                self._depth, 
                self.supported_actions,
                self.states,
                self.bounds
            ]

    @property
    def states(self) -> str:
        return ', '.join(self._control.states)

    @property
    def supported_actions(self) -> str:
        acts = []
        acc_acts = AccessibleActions()
        self._control.bridge.getAccessibleActions(
            self._control.vmid, self._control.accessible_context, byref(acc_acts)
        )
        for i in range(acc_acts.actionsCount):
            acts.append(acc_acts.actionInfo[i].name)
        return ', '.join(acts)

    @property
    def data(self) -> List[List]:
        if self._data is None:
            self._data = [
                [   
                    "Role", 
                    "Name",
                    "Description",
                    "Depth", 
                    "Supported Actions",
                    "States",
                    "Bounds"
                ], 
                self.properties
            ] 
        return self._data

    @property
    def model(self) -> QAbstractTableModel:
        if self._model is None:
            self._model = JABPropertyTableModel(self.data)
        return self._model

class JABSelectorHelper:

    def _is_control_equal(self, control: JElement, other: JElement, attributes: Dict) -> bool:
        for attribute, value in attributes.items():
            if getattr(other, attribute) != value:
                return False
        if 'name' not in attributes and (value:=control.name) != other.name:
            attributes['name'] = value
            return False
        return True

    def show_selectors_from_control(self, control: JElement, window):
        depth = 0
        selectors = deque()
        while control:
            attributes = {}
            attributes["role"] = control.role
            if (value := control.name):
                attributes["name"] = value
            parent = control.get_accessible_parent_from_context()
            if parent:
                index_in_parent = control.index_in_parent - 1
                sibling = parent.get_accessible_child_from_context(index_in_parent)
                index = 1
                pos = 0
                sibling_has_children = False
                while sibling:
                    pos += 1
                    if self._is_control_equal(control, sibling, attributes):
                        index += 1
                    if sibling.children_count > 0:
                        sibling_has_children = True
                    index_in_parent -= 1
                    sibling = parent.get_accessible_child_from_context(index_in_parent)
                selectors.appendleft((control, depth, index, sibling_has_children, pos, attributes))
            else:
                for i, top_window in enumerate(window.root_item.control.GetChildren()):
                    if top_window.NativeWindowHandle == control.hwnd:
                        selectors.appendleft((control, depth, 1, False, i, attributes))
                        break
            control = parent
            depth += 1

        window.refresh()
        tree_item = window.root_item

        control: JElement
        for control, depth, index, sibling_has_children, pos, attributes in selectors:
            window.show_children(tree_item)
            tree_item = tree_item.child(pos)

            depth = len(selectors) - depth

            selector_str = '<java'
            for attr, value in attributes.items():
                if attr in attributes:
                    selector_str += f" {attr}='{value}'"
            if index > 1 and depth > 1: # top window no need index
                selector_str += f' idx={index}'
            selector_str += f' depth={depth}>'
            list_item = QtWidgets.QListWidgetItem(selector_str)

            if sibling_has_children or depth == len(selectors) or depth == 1:
                list_item.setCheckState(QtCore.Qt.Checked)
                tree_item.setFont(0, window.checked_font)
                list_item.setFont(window.checked_font)
            else:
                list_item.setCheckState(QtCore.Qt.Unchecked)

            window.selector_list.addItem(list_item)
        window.tree.scrollToItem(tree_item, QtWidgets.QAbstractItemView.PositionAtCenter)
        self.generate_code_from_selectors(window)
        window.show_properties(tree_item)

    def generate_code_from_selectors(self, window):
        window.selector_code_area.clear()
        depth = 0
        code = ''
        checked_rows = 0
        for i in range(window.selector_list.count()):
            item = window.selector_list.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                item.setFont(window.checked_font)
                _, attributes = self.parse_selector(item.text()) # parse selector
                string = "  {"
                depth_ = attributes['depth'] - depth
                depth = attributes.pop('depth')
                index = attributes.pop('found_index', None)
                for attr, value in attributes.items():
                    string += f"{attr}: '{value}', "
                if index is not None:
                    string += f"found_index: {index}, "
                string += f"depth: {depth_}"
                string += "},\n"
                if i > 0:
                    code += string
                    checked_rows += 1
            else:
                item.setFont(window.unchecked_font)
        if checked_rows > 1:
            prefix = 'jdriver.find_element_by_levels((\n'
            surfix = '\n))'
        else:
            prefix = 'jdriver.find_element_by_levels(\n'
            surfix = '\n)'
        code = prefix + code[:-2] + surfix
        window.selector_code_area.setPlainText(code)
        window.copy_btn.setVisible(True)

    @staticmethod
    def parse_selector(selector: str) -> Tuple[str, Mapping]:
        pat = re.compile(
            "<java role='(?P<role>.*?)'( name='(?P<name>.*?)')?"
            "( idx=(?P<idx>\d+?))? depth=(?P<depth>\d+?)>",
            re.DOTALL
            )
        m = pat.match(selector)
        if m:
            try:
                attributes = {}
                for k, v in m.groupdict().items():
                    if k == 'role' and v is not None:
                        attributes['role'] = v
                    elif k == 'name' and v is not None:
                        attributes['name'] = v
                    elif k == 'idx' and v is not None:
                        attributes['found_index'] = int(v)
                    elif k == 'depth':
                        attributes['depth'] = int(v)  
                return attributes['role'], attributes
            except Exception as e:
                raise ParseSelectorError('Cannot parse selector: %s' % selector) from e       

        raise ParseSelectorError('Cannot parse selector: %s' % selector)