from typing import Dict, List
from PySide6.QtWidgets import QTreeWidgetItem, QTableView
from PySide6.QtCore import QAbstractTableModel, Qt

class PropertyTableModel(QAbstractTableModel):

    Columns = ['Property', 'Value']

    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data[index.column()][index.row()]
            return value
    
    def rowCount(self, index):
        return len(self._data[0])

    def columnCount(self, index):
        return len(self._data)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.Columns[section]

    def flags(self, index):
        if index.column() == 1:
            return super().flags(index) | Qt.ItemIsEditable
        return super().flags(index)

class UITreeItem(QTreeWidgetItem):

    def addChild(self, child: QTreeWidgetItem) -> None:
        return super().addChild(child)

    @property
    def control(self):
        raise NotImplementedError

    @property
    def properties(self) -> Dict:
        raise NotImplementedError

    @property
    def states(self) -> List:
        raise NotImplementedError

    @property
    def data(self) -> List[List]:
        raise NotImplementedError

    @property
    def model(self) -> QAbstractTableModel:
        raise NotImplementedError

    def update_property_table(self, table: QTableView) -> None:
        self.data[1] = self.properties
        if self.model is table.model():
            return
        table.setModel(self.model)