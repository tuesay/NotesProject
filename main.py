import sys
import sqlite3

from noteEditUi import Ui_noteEdit

from notesUi import Ui_Notes

from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog, QListWidget, QListWidgetItem


class NoteEdit(QDialog, Ui_noteEdit):
    def __init__(self):
        super().__init__()

        self.setupUi(self)

        self.initUi()

    def initUi(self):

        self.showImgPlace.clicked.connect(self.show_place)
        self.imageAdd.hide()
        self.imageDisplay.hide()

        self.noteSave.clicked.connect(self.note_save)
        self.noteCancel.clicked.connect(self.note_cancel)

    def show_place(self):
        if self.showImgPlace.text() == '>>>':
            self.imageAdd.show()
            self.imageDisplay.show()
            self.showImgPlace.setText('<<<')

        elif self.showImgPlace.text() == '<<<':
            self.imageAdd.hide()
            self.imageDisplay.hide()
            self.showImgPlace.setText('>>>')

    def note_save(self):
        name = self.noteName.text()
        text = self.noteText.toPlainText()

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        if len(cur.execute("SELECT name FROM notes WHERE name = ?", (name, )).fetchall()) > 1:
            cur.execute("UPDATE notes SET name = ?, text = ?", (name, text))

        elif name != cur.execute("SELECT name FROM notes WHERE name = ?", (name, )).fetchone():
            cur.execute("INSERT INTO notes(name, text) VALUES(?, ?)", (name, text))

        con.commit()
        con.close()
        self.close()

    def note_cancel(self):
        self.close()


class Notes(QMainWindow, Ui_Notes):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.initUi()

        self.list_update()

    def initUi(self):
        self.createNote.clicked.connect(self.note_creation)
        self.refreshButton.clicked.connect(self.list_update)

    def list_update(self):
        self.noteList.clear()
        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()
        ids = cur.execute("SELECT id FROM notes").fetchall()
        for i in ids:
            self.noteList.addItem(QListWidgetItem(cur.execute("SELECT name FROM notes WHERE id = ?", (i[0], )).fetchone()[0]))
        con.close()

    def note_creation(self):
        self.note_window = NoteEdit()
        self.note_window.exec()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Notes()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
