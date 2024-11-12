import sqlite3
import sys

import pyperclip

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QMenu, QInputDialog, \
    QListWidget

from noteEdit import NoteEdit
from notesUi import Ui_Notes


class Notes(QMainWindow, Ui_Notes):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.initUi()

        self.list_update()
        self.tag_update()

    def initUi(self):
        self.noteList.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        self.noteList.doubleClicked.connect(self.note_redaction)
        self.tagSelect.currentIndexChanged.connect(self.list_update)

        self.noteList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.noteList.customContextMenuRequested.connect(self.show_list_context)

        self.tagSelect.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tagSelect.customContextMenuRequested.connect(self.show_tag_context)

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

        for i in ids[::-1]:
            name = cur.execute("SELECT name FROM notes WHERE id = ?", (i[0], )).fetchone()[0]

            self.noteList.addItem(QListWidgetItem(f'{name}'))

        con.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return and self.noteList.currentItem() is not None:
            self.note_redaction()

    def show_list_context(self, pos):
        global_pos = self.noteList.mapToGlobal(pos)
        index = self.noteList.indexAt(pos)

        if not index.isValid():
            context_menu = QMenu()
            create = QAction('Создать заметку', self)
            create.triggered.connect(self.note_creation)
            context_menu.addAction(create)
            context_menu.exec(global_pos)
        else:
            name = self.noteList.currentItem().text()
            items = self.noteList.selectedItems()

            con = sqlite3.connect('note.sqlite')
            tag_id = con.cursor().execute("SELECT tag_id FROM notes WHERE name = ?", (name, )).fetchone()[0]
            tag_name = con.cursor().execute("SELECT tag_name FROM tags WHERE tag_id = ?", (tag_id, )).fetchone()
            con.close()

            context_menu = QMenu()

            if tag_name is not None:
                tag_name = tag_name[0]
                tag_name = QAction(f'Тег - {tag_name}', self)
            else:
                tag_name = QAction('Тег - Без тега', self)

            tag_name.setEnabled(False)

            delete = QAction('Удалить заметку', self)
            edit = QAction('Редактировать', self)
            copy = QAction('Копировать имя', self)
            tag_assign = QAction('Присвоить тег', self)
            tag_unassign = QAction('Отсоединить тег', self)

            delete.triggered.connect(self.note_delete)
            edit.triggered.connect(self.note_redaction)
            copy.triggered.connect(self.note_copy)
            tag_assign.triggered.connect(self.tag_assign)
            tag_unassign.triggered.connect(self.tag_unassign)

            if len(items) > 1:
                delete = QAction('Удалить заметки', self)
                tag_unassign = QAction('Отсоединить заметки от тегов', self)

                delete.triggered.connect(self.note_delete)
                tag_unassign.triggered.connect(self.tag_unassign)
                context_menu.addActions([delete, tag_unassign])
            else:
                if tag_id is None:
                    context_menu.addAction(tag_name)
                    context_menu.addSeparator()
                    context_menu.addActions([edit, copy, tag_assign, delete])
                else:
                    context_menu.addAction(tag_name)
                    context_menu.addSeparator()
                    context_menu.addActions([edit, copy, tag_unassign, delete])
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
        items = self.noteList.selectedItems()

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        if len(items) > 1:
            for name in items:
                cur.execute("UPDATE notes SET tag_id = NULL WHERE name = ?", (name.text(),))

        else:
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
        items = self.noteList.selectedItems()

        con = sqlite3.connect('note.sqlite')

        if len(items) > 1:
            for name in items:
                print(f'deleted: {name.text()}')
                con.cursor().execute("DELETE FROM notes WHERE name = ?", (name.text(),))

        else:
                print(f'deleted: {name}')
                con.cursor().execute("DELETE FROM notes WHERE name = ?", (name,))

        con.commit()
        con.close()

        self.list_update()

    def note_creation(self):
        if self.tagSelect.currentText() != 'Без тега':
            tag = self.tagSelect.currentText()
        else:
            tag = None
        print('creating a new note with a tag:', tag)
        dialog = NoteEdit(name=None, tag=tag)
        dialog.exec()
        self.list_update()

    def note_redaction(self):
        name = self.noteList.currentItem().text()
        print(f'redacting: {name}')
        dialog = NoteEdit(name)
        dialog.exec()
        self.list_update()

    def note_copy(self):
        pyperclip.copy(self.noteList.currentItem().text())


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Notes()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
