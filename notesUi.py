

from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Notes(object):
    def setupUi(self, Notes):
        Notes.setObjectName("Notes")
        Notes.resize(615, 470)
        Notes.setMinimumSize(QtCore.QSize(400, 310))
        Notes.setMouseTracking(False)
        self.centralwidget = QtWidgets.QWidget(parent=Notes)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setContentsMargins(12, 12, 12, 12)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName("gridLayout")
        self.searchLine = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.searchLine.setObjectName("searchLine")
        self.gridLayout.addWidget(self.searchLine, 1, 0, 1, 2)
        self.tagSelect = QtWidgets.QComboBox(parent=self.centralwidget)
        self.tagSelect.setObjectName("tagSelect")
        self.gridLayout.addWidget(self.tagSelect, 1, 3, 1, 1)
        self.sortBy = QtWidgets.QComboBox(parent=self.centralwidget)
        self.sortBy.setObjectName("sortBy")
        self.sortBy.addItem("")
        self.sortBy.addItem("")
        self.gridLayout.addWidget(self.sortBy, 1, 2, 1, 1)
        self.noteList = QtWidgets.QListWidget(parent=self.centralwidget)
        self.noteList.setMinimumSize(QtCore.QSize(0, 0))
        self.noteList.setObjectName("noteList")
        self.gridLayout.addWidget(self.noteList, 2, 0, 2, 4)
        Notes.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(parent=Notes)
        self.statusbar.setObjectName("statusbar")
        Notes.setStatusBar(self.statusbar)

        self.retranslateUi(Notes)
        QtCore.QMetaObject.connectSlotsByName(Notes)

    def retranslateUi(self, Notes):
        _translate = QtCore.QCoreApplication.translate
        Notes.setWindowTitle(_translate("Notes", "Заметки"))
        self.searchLine.setToolTip(_translate("Notes", "Поиск по имени"))
        self.sortBy.setItemText(0, _translate("Notes", "Недавно созданные"))
        self.sortBy.setItemText(1, _translate("Notes", "Алфавит"))
