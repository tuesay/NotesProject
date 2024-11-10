import sqlite3

from noteEditUi import Ui_noteEdit

from PyQt6.QtWidgets import QDialog, QErrorMessage


class NoteEdit(QDialog, Ui_noteEdit):
    def __init__(self, name=None):
        super().__init__()

        self.name = name

        self.setupUi(self)

        self.initUi()


    def initUi(self):

        self.showImgPlace.clicked.connect(self.show_place)
        self.imageAdd.hide()
        self.imageDisplay.hide()

        self.noteSave.clicked.connect(self.note_save)
        self.noteCancel.clicked.connect(self.note_cancel)

        if self.name != None:
            con = sqlite3.connect('note.sqlite')
            cur = con.cursor()

            self.noteName.setReadOnly(True)
            self.noteName.setText(self.name)
            self.noteText.setText(cur.execute("SELECT text FROM notes WHERE name = ?", (self.name,)).fetchone()[0])


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
        try:
            if self.name is None:

                cur.execute("INSERT INTO notes(name, text) VALUES(?, ?)", (name, text))

            else:

                cur.execute("UPDATE notes SET text = ?", (text, ))

        except sqlite3.IntegrityError:
            name_unique = QErrorMessage.exec(self)


        con.commit()
        con.close()
        self.close()
        return name

    def note_cancel(self):
        self.close()