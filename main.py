import sys
import sqlite3

from PyQt6.QtGui import QAction

from noteEdit import NoteEdit
from notesUi import Ui_Notes

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QMenu, QInputDialog


class Notes(QMainWindow, Ui_Notes):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.initUi()

        self.list_update()
        self.tag_update()

    def initUi(self):
        self.noteList.doubleClicked.connect(self.note_redaction)
        self.tagSelect.currentIndexChanged.connect(self.list_update)

        self.noteList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.noteList.customContextMenuRequested.connect(self.show_list_context)

        self.tagSelect.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tagSelect.customContextMenuRequested.connect(self.show_tag_context)

    def show_list_context(self, pos):
        global_pos = self.noteList.mapToGlobal(pos)
        index = self.noteList.indexAt(pos)

        if not index.isValid():
            context_menu = QMenu()
            create = QAction('Создать', self)
            create.triggered.connect(self.note_creation)
            context_menu.addAction(create)
            context_menu.exec(global_pos)
        else:
            name = self.noteList.currentItem().text()

            con = sqlite3.connect('note.sqlite')
            tag_id = con.cursor().execute("SELECT tag_id FROM notes WHERE name = ?", (name, )).fetchone()[0]
            con.close()

            context_menu = QMenu()
            delete = QAction('Удалить', self)
            edit = QAction('Редактировать', self)
            tag_assign = QAction('Присвоить тег', self)
            tag_unassign = QAction('Отсоединить тег', self)

            delete.triggered.connect(self.note_delete)
            edit.triggered.connect(self.note_redaction)
            tag_assign.triggered.connect(self.tag_assign)
            tag_unassign.triggered.connect(self.tag_unassign)

            if tag_id is None:
                context_menu.addActions([delete, edit, tag_assign])
            else:
                context_menu.addActions([delete, edit, tag_unassign])
            context_menu.exec(global_pos)

    def show_tag_context(self, pos):
        global_pos = self.tagSelect.mapToGlobal(pos)

        context_menu = QMenu()

        create = QAction('Создать тег', self)
        delete = QAction('Удалить тег', self)

        create.triggered.connect(self.tag_creation)
        delete.triggered.connect(self.tag_delete)

        context_menu.addAction(create)
        context_menu.addAction(delete)

        context_menu.exec(global_pos)

    def tag_update(self):
        self.tagSelect.clear()

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()
        self.tagSelect.addItem('Без тега')
        tags = cur.execute("SELECT tag_name FROM tags").fetchall()
        for i in tags:
            self.tagSelect.addItem(i[0])

    def list_update(self):
        self.noteList.clear()

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        tag = self.tagSelect.currentText()
        if tag == 'Без тега':
            ids = cur.execute("SELECT id FROM notes").fetchall()
        else:
            ids = cur.execute("SELECT id FROM notes WHERE tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?)",
                              (tag, )).fetchall()

        for i in ids:
            name = cur.execute("SELECT name FROM notes WHERE id = ?", (i[0], )).fetchone()[0]

            self.noteList.addItem(QListWidgetItem(f'{name}'))

        con.close()

    def tag_creation(self):
        name, ok_pressed = QInputDialog.getText(self, "Введите название тега",
                                                "Название тега:")

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        if ok_pressed:
            try:

                cur.execute("INSERT INTO tags(tag_name) VALUES(?)", (name,))

            except sqlite3.IntegrityError:
                name = name + '~'

                cur.execute("INSERT INTO tags(tag_name) VALUES(?)", (name,))

            con.commit()
            con.close()
            self.tag_update()

    def tag_assign(self):
        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        tags = map(lambda x: x[0], cur.execute("SELECT tag_name FROM tags").fetchall())

        tag, ok_pressed = QInputDialog.getItem(self, 'Выбор тега', 'Выберите тег:', tags,
                                               editable=False)

        if ok_pressed:
            name = self.noteList.currentItem().text()
            cur.execute("UPDATE notes SET tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?) WHERE name = ?",
                        (tag, name))
            con.commit()
        con.close()


    def tag_unassign(self):
        name = self.noteList.currentItem().text()

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        cur.execute("UPDATE notes SET tag_id = NULL WHERE name = ?", (name, ))
        con.commit()
        con.close()
        self.list_update()

    def tag_delete(self):
        tag_name = self.tagSelect.currentText()

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()
        cur.execute('DELETE FROM tags WHERE tag_name = ?', (tag_name, ))
        con.commit()
        con.close()

        self.tag_update()

    def note_delete(self):
        name = self.noteList.currentItem().text()
        con = sqlite3.connect('note.sqlite')
        con.cursor().execute("DELETE FROM notes WHERE name = ?", (name,))
        con.commit()
        con.close()
        self.list_update()

    def note_creation(self):
        print('creating a new note')
        dialog = NoteEdit()
        dialog.exec()
        self.list_update()

    def note_redaction(self):
        name = self.noteList.currentItem().text()
        print(f'redacting: {name}')
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
