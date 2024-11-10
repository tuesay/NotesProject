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
        self.noteList.doubleClicked.connect(self.note_redaction)

        self.list_context_menu()

    def list_context_menu(self):
        self.noteList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.noteList.customContextMenuRequested.connect(self.show_context)

    def show_context(self, pos):
        global_pos = self.noteList.mapToGlobal(pos)
        index = self.noteList.indexAt(pos)

        if not index.isValid():
            context_menu = QMenu()
            create_action = QAction('Создать', self)
            create_action.triggered.connect(self.note_creation)
            context_menu.addAction(create_action)
            context_menu.exec(global_pos)
        else:
            context_menu = QMenu()
            delete_action = QAction('Удалить', self)
            edit_action = QAction('Редактировать', self)

            delete_action.triggered.connect(self.note_delete)
            edit_action.triggered.connect(self.note_redaction)

            context_menu.addActions([delete_action, edit_action])
            context_menu.exec(global_pos)


    def note_delete(self):
        name = self.noteList.currentItem().text()
        con = sqlite3.connect('note.sqlite')
        con.cursor().execute("DELETE FROM notes WHERE name = ?", (name,))
        con.commit()
        con.close()
        self.list_update()

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
        self.list_update()

    def note_redaction(self):
        name = self.noteList.currentItem().text()
        dialog = NoteEdit(name)
        dialog.exec()
        self.list_update()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Notes()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
