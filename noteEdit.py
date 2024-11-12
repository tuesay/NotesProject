import sqlite3

from noteEditUi import Ui_noteEdit

from PyQt6.QtWidgets import QDialog, QMessageBox


class NoteEdit(QDialog, Ui_noteEdit):
    def __init__(self, name=None, tag=None):
        super().__init__()

        self.name = name
        self.tag = tag

        self.setupUi(self)

        self.initUi()


    def initUi(self):

        self.showImgPlace.clicked.connect(self.show_place)
        self.imageAdd.hide()
        self.imageDisplay.hide()

        self.noteSave.clicked.connect(self.note_save)
        self.noteCancel.clicked.connect(self.note_cancel)
        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        self.tagSet.addItem('Без тега')

        tags = cur.execute("SELECT tag_name FROM tags").fetchall()
        for i in tags:
            self.tagSet.addItem(i[0])

        if self.name != None:
            self.noteName.setText(self.name)
            self.noteText.setText(cur.execute("SELECT text FROM notes WHERE name = ?", (self.name,)).fetchone()[0])
            tag = cur.execute("SELECT tag_name FROM tags WHERE tag_id = (SELECT tag_id FROM notes WHERE name = ?)", (self.name,)).fetchone()
            if tag is None:
                self.tagSet.setCurrentText('Без тега')
            else:
                self.tagSet.setCurrentText(tag[0])
        else:
            self.tagSet.setCurrentText(self.tag)

        con.close()

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
        if self.tagSet == 'Без тега':
            tag = 'NULL'
        else:
            tag = self.tagSet.currentText()

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()
        if self.name is None:
            try:
                cur.execute("INSERT INTO notes(name, text, tag_id) VALUES(?, ?, (SELECT tag_id FROM tags WHERE tag_name = ?))", (name, text, tag))
                con.commit()
                con.close()
            except sqlite3.IntegrityError:
                name = name + '~'
                cur.execute("INSERT INTO notes(name, text, tag_id) VALUES(?, ?, (SELECT tag_id FROM tags WHERE tag_name = ?))", (name, text, tag))
                con.commit()
                con.close()
        else:
            try:
                cur.execute("UPDATE notes SET name = ?, text = ?, tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?) WHERE name = ?", (name, text, tag, self.name))
                con.commit()
                con.close()
            except sqlite3.IntegrityError:
                name = name + '~'
                cur.execute("UPDATE notes SET name = ?, text = ?, tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?) WHERE name = ?", (name, text, tag, self.name))
                con.commit()
                con.close()

        self.close()
        print(f'saved note: {name} with tag: {tag}')

    def note_cancel(self):
        self.close()