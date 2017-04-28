from PyQt5 import QtCore


class Model(QtCore.QAbstractListModel):
    def __init__(self, items, roles, parent=None):
        super(Model, self).__init__(parent)
        self._items = [items or list()]
        self._roles = {
            QtCore.Qt.UserRole + index: role.encode("utf-8")
            for index, role in enumerate(roles)
        }

    def append(self, item):
        self.beginInsertRows(QtCore.QModelIndex(),
                             self.rowCount(),
                             self.rowCount())
        self._items[-1].append(item)
        self.endInsertRows()

    def push(self, items):
        self.beginResetModel()
        self._items.append(items)
        self.endResetModel()

    def pop(self):
        self.beginResetModel()
        self._items.pop()
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._items[-1])

    def data(self, index, role=QtCore.QModelIndex()):
        key = self._roles[role].decode("utf-8")
        item = self._items[-1][index.row()]
        return item.get(key)

    def roleNames(self):
        return self._roles
