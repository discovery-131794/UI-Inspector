from __future__ import annotations
from collections import deque
import re
from typing import Dict, List, Mapping, Tuple
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QTreeWidgetItem
from PySide6.QtCore import QAbstractTableModel
from uiautomation import Control, PatternIdNames, PatternId
from win32con import *
from common.exceptions import ParseSelectorError
from win32.functions import *
from win32.structures import *
from ..base import PropertyTableModel, UITreeItem

class UIAPropertyTableModel(PropertyTableModel):
    pass


class UIATreeItem(UITreeItem):

    def __init__(self, control: Control = None, parent = None, display_name = None) -> None:
        if control is None:
            return
        self._depth = getattr(parent, "_depth", -1) + 1
        self._control = control
        self._control_type = control.ControlTypeName.replace("Control", "")
        self._name = control.Name
        self._display_name = self._control_type + " " + self._name.title()
        super().__init__(parent, [display_name or self._display_name])
        self._class_name = control.ClassName
        self._id = control.AutomationId

        self._data = None
        self._model = None

    def addChild(self, child: QTreeWidgetItem) -> None:
        return super().addChild(child)

    @property
    def control(self):
        return self._control

    @property
    def bounds(self) -> str:
        rect = self._control.BoundingRectangle
        return f'X={rect.left}, Y={rect.top}, Width={rect.width()}, Height={rect.height()}'

    @property
    def properties(self):
        return [
                self._control_type, 
                self._id,
                self._name,
                self._class_name, 
                self._depth, 
                self.supported_patterns,
                self.states,
                self.bounds
            ]

    @property
    def states(self) -> str:
        st = []
        if not self._control.IsOffscreen:
            st.append('visible')
        if self._control.IsEnabled:
            st.append('enabled')
        if self._control.IsKeyboardFocusable:
            st.append('focusable')
        if self._control.HasKeyboardFocus:
            st.append('focused')
        if (pat:=self._control.GetPattern(PatternId.ValuePattern)) and not pat.IsReadOnly and 'enabled' in st:
            st.append('editable')

        return ', '.join(st)

    @property
    def supported_patterns(self) -> str:
        patterns = list(
                dict(
                    filter(
                        lambda t: t[1], [(
                            name, self._control.GetPattern(id_))
                             for id_, name in PatternIdNames.items()])).keys())

        return ', '.join(patterns)

    @property
    def data(self) -> List[List]:
        if self._data is None:
            self._data = [
                [   
                    "Control Type", 
                    "Automationid",
                    "Name",
                    "Cls", 
                    "Depth", 
                    "Supported Patterns",
                    "States",
                    "Bounds"
                ], 
                self.properties
            ] 
        return self._data

    @property
    def model(self) -> QAbstractTableModel:
        if self._model is None:
            self._model = UIAPropertyTableModel(self.data)
        return self._model


class UIASelectorHelper:

    def _is_control_equal(self, control: Control, other: Control, attributes: Dict) -> bool:
        if control.ControlType != other.ControlType:
            return False
        for attribute, value in attributes.items():
            if getattr(other, attribute) != value:
                return False
        if (value:=control.AutomationId) and value != other.AutomationId:
            attributes['AutomationId'] = value
            return False
        if 'Name' not in attributes and (value:=control.Name) != other.Name:
            attributes['Name'] = value
            return False
        if 'ClassName' not in attributes and (value:=control.ClassName) != other.ClassName:
            attributes['ClassName'] = value
            return False
        return True

    def show_selectors_from_control(self, control: Control, window):
        depth = 0
        selectors = deque()
        while control:
            attributes = {}
            if (value := control.Name):
                attributes["Name"] = value
            if (value := control.ClassName):
                attributes["ClassName"] = value
            if not attributes and (value := control.AutomationId):
                attributes['AutomationId'] = value
            parent = control.GetParentControl()
            if parent:
                sibling = control.GetPreviousSiblingControl()
                index = 1
                pos = 0
                sibling_has_children = False
                while sibling:
                    pos += 1
                    if self._is_control_equal(control, sibling, attributes):
                        index += 1
                    if sibling.GetFirstChildControl():
                        sibling_has_children = True
                    
                    sibling = sibling.GetPreviousSiblingControl()
                selectors.appendleft((control, depth, index, sibling_has_children, pos, attributes))
            control = parent
            depth += 1

        window.refresh()
        tree_item = window.root_item
        attr_display_map = {
            'Name': 'name',
            'ClassName': 'cls',
            'AutomationId': 'id'
        }
        for control, depth, index, sibling_has_children, pos, attributes in selectors:
            window.show_children(tree_item)
            tree_item = tree_item.child(pos)

            depth = len(selectors) - depth
            control_type = control.ControlTypeName.replace('Control', '')

            selector_str = f'<{control_type}'
            for attr, display in attr_display_map.items():
                if attr in attributes:
                    selector_str += f" {display}='{attributes[attr]}'"
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
        code = 'uiautomation\n'
        depth = 0
        for i in range(window.selector_list.count()):
            item = window.selector_list.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                item.setFont(window.checked_font)
                control_type, attributes = self.parse_selector(item.text()) # parse selector
                string = f".{control_type}("
                depth_ = attributes['Depth'] - depth
                depth = attributes.pop('Depth')
                index = attributes.pop('foundIndex', None)
                for attr, value in attributes.items():
                    string += f"{attr}='{value}', "
                if index is not None:
                    string += f"foundIndex={index}, "
                string += f"Depth={depth_})\n"
                code += string
            else:
                item.setFont(window.unchecked_font)
        window.selector_code_area.setPlainText(code)
        window.copy_btn.setVisible(True)

    @staticmethod
    def parse_selector(selector: str) -> Tuple[str, Mapping]:
        pat = re.compile(
            "<(?P<control>.+?)( name='(?P<name>.*?)')?( cls='(?P<cls>.*?)')?( id='(?P<id>.*?)')?"
            "( idx=(?P<idx>\d+?))? depth=(?P<depth>\d+?)>",
            re.DOTALL
            )
        m = pat.match(selector)
        if m:
            try:
                control_type = m.group('control') + 'Control'
                attributes = {}
                for k, v in m.groupdict().items():
                    if k == 'name' and v is not None:
                        attributes['Name'] = v
                    elif k == 'cls' and v is not None:
                        attributes['ClassName'] = v
                    elif k == 'id' and v is not None:
                        attributes['AutomationId'] = v
                    elif k == 'idx' and v is not None:
                        attributes['foundIndex'] = int(v)
                    elif k == 'depth':
                        attributes['Depth'] = int(v)  
                return control_type, attributes
            except Exception as e:
                raise ParseSelectorError('Cannot parse selector: %s' % selector) from e       

        raise ParseSelectorError('Cannot parse selector: %s' % selector)

