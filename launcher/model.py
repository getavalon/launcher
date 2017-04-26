from PyQt5 import QtCore


class Model(QtCore.QAbstractListModel):
    def __init__(self, items=None, parent=None):
        super(Model, self).__init__(parent)
        self._items = items or list()

    def append(self, item):
        self.beginInsertRows(QtCore.QModelIndex(),
                             self.rowCount(),
                             self.rowCount())
        self._items.append(item)
        self.endInsertRows()

    def rowCount(self, parent=None):
        return len(self._items)

    def data(self, index, role=QtCore.QModelIndex()):
        if role == QtCore.Qt.UserRole + 0:
            return self._items[index.row()]

    def roleNames(self):
        return {
            QtCore.Qt.UserRole + 0: b"line",
        }
