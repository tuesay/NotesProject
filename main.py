import sys
import sqlite3

from PyQt6.QtGui import QAction

from noteEdit import NoteEdit
from notesUi import Ui_Notes

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidget, QListWidgetItem, QMenu


class Notes(QMainWindow, Ui_Notes):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.initUi()

        self.list_update()

    def initUi(self):
        self.createNote.clicked.connect(self.note_creation)
        self.refreshButton.clicked.connect(self.list_update)
        self.noteList.doubleClicked.connect(self.note_redaction)

        self.list_context_menu()

    def list_context_menu(self):
        self.noteList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.noteList.customContextMenuRequested.connect(self.show_context)

    def show_context(self, pos):
        global_pos = self.noteList.mapToGlobal(pos)

        index = self.noteList.indexAt(pos)
        if not index.isValid():
            return

        self.context_menu = QMenu()

        delete = QAction('Удалить', self)
        edit = QAction('Редактировать', self)

        delete.triggered.connect(self.note_delete)
        edit.triggered.connect(self.note_redaction)

        self.context_menu.addAction(delete)
        self.context_menu.addAction(edit)

        self.context_menu.exec(global_pos)


    def note_delete(self):
        pass

    def list_update(self):
        self.noteList.clear()
        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()
        ids = cur.execute("SELECT id FROM notes").fetchall()
        for i in ids:
            self.noteList.addItem(QListWidgetItem(cur.execute("SELECT name FROM notes WHERE id = ?", (i[0], )).fetchone()[0]))
        con.close()

    def note_creation(self):
        dialog = NoteEdit()
        dialog.exec()
        print(dialog.note_save())

    def note_redaction(self):
        name = self.noteList.currentItem().text()
        dialog = NoteEdit(name)
        dialog.exec()



def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Notes()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
