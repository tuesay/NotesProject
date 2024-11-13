import sqlite3

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from noteEditUi import Ui_noteEdit

from PyQt6.QtWidgets import QDialog, QMenu, QInputDialog, QErrorMessage, QMessageBox


class NoteEdit(QDialog, Ui_noteEdit):
    def __init__(self, name=None, tag=None):
        super().__init__()

        self.name = name
        self.tag = tag

        self.setupUi(self)

        self.initUi()

    def initUi(self):
        self.showImgPlace.clicked.connect(self.show_place)

        self.tagSet.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.tagSet.customContextMenuRequested.connect(self.show_tag_context)

        self.imageAdd.hide()
        self.imageDisplay.hide()

        self.noteSave.clicked.connect(self.note_save)
        self.noteCancel.clicked.connect(self.note_cancel)

        self.update_data()

    def update_data(self):
        # Функция отвечает за обновление данных уже существующей заметки и
        # обновление существующих тегов в БД
        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        self.tagSet.clear()

        self.tagSet.addItem('Без тега')

        tags = cur.execute("SELECT tag_name FROM tags").fetchall()
        for i in tags:
            self.tagSet.addItem(i[0])

        if self.name is not None:  # заполнение данных уже существующей заметки
            self.noteName.setText(self.name)
            self.noteText.setText(
                cur.execute(
                    "SELECT text FROM notes WHERE name = ?",
                    (self.name,
                     )).fetchone()[0])
            tag = cur.execute(
                "SELECT tag_name FROM tags WHERE tag_id = (SELECT tag_id FROM notes WHERE name = ?)",
                (self.name,
                 )).fetchone()
            if tag is None:
                self.tagSet.setCurrentText('Без тега')
            else:
                self.tagSet.setCurrentText(tag[0])
        else:
            self.tagSet.setCurrentText(self.tag)

        con.close()

    # обработка дубликатов имени заметки
    def duplicate_handle_notes(self, name):
        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        name = name + '~'
        name_tuple = (name,)
        duplicate = cur.execute(
            "SELECT name FROM notes WHERE name = ?", (name,)).fetchone()
        while name_tuple == duplicate:
            name = name + '~'
            name_tuple = (name,)
            duplicate = cur.execute(
                "SELECT name FROM notes WHERE name = ?", (name,)).fetchone()

        con.close()

        return name

    def duplicate_handle_tag(self, name):  # обработка дубликатов имени тега
        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        name = name + '~'
        name_tuple = (name,)
        duplicate = cur.execute(
            "SELECT tag_name FROM tags WHERE tag_name = ?", (name,)).fetchone()
        while name_tuple == duplicate:
            name = name + '~'
            name_tuple = (name,)
            duplicate = cur.execute(
                "SELECT tag_name FROM tags WHERE tag_name = ?", (name,)).fetchone()

        con.close()

        return name

    def show_tag_context(self, pos):  # контекстное меню для QComboBox
        global_pos = self.tagSet.mapToGlobal(pos)

        context_menu = QMenu()

        create = QAction('Создать тег', self)
        delete = QAction('Удалить тег', self)

        context_menu.addAction(create)
        context_menu.addAction(delete)

        create.triggered.connect(self.tag_creation)
        delete.triggered.connect(self.tag_delete)

        context_menu.exec(global_pos)

    def show_place(self):  # in progress
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
                cur.execute(
                    "INSERT INTO notes(name, text, tag_id) "
                    "VALUES(?, ?, (SELECT tag_id FROM tags WHERE tag_name = ?))", (name, text, tag))

                con.commit()
                con.close()
            except sqlite3.IntegrityError:
                name = self.duplicate_handle_notes(name)
                cur.execute(
                    "INSERT INTO notes(name, text, tag_id) "
                    "VALUES(?, ?, (SELECT tag_id FROM tags WHERE tag_name = ?))", (name, text, tag))

                con.commit()
                con.close()
        else:
            try:
                cur.execute(
                    "UPDATE notes SET name = ?, text = ?, "
                    "tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?) WHERE name = ?",
                    (name,
                     text,
                     tag,
                     self.name))

                con.commit()
                con.close()
            except sqlite3.IntegrityError:
                name = self.duplicate_handle_notes(name)

                cur.execute(
                    "UPDATE notes SET name = ?, text = ?, "
                    "tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?)"
                    " WHERE name = ?", (name, text, tag, self.name))

                con.commit()
                con.close()

        self.close()
        print(f'saved note: {name} with tag: {tag}')

    def note_cancel(self):
        self.close()

    def tag_creation(self):
        # Возможно создать тег при создании и/или редактировании заметки. Это улучшает возможный
        # пользовательский опыт
        name, ok_pressed = QInputDialog.getText(self, "Введите название тега",
                                                "Название тега:")

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        if ok_pressed:
            try:

                cur.execute("INSERT INTO tags(tag_name) VALUES(?)", (name,))

            except sqlite3.IntegrityError:
                name = self.duplicate_handle_tag(name)

                cur.execute("INSERT INTO tags(tag_name) VALUES(?)", (name,))

        con.commit()
        con.close()

        self.update_data()

    def tag_delete(self):  # удаление тега
        tag_name = self.tagSet.currentText()

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()
        cur.execute('DELETE FROM tags WHERE tag_name = ?', (tag_name,))
        con.commit()
        con.close()

        self.update_data()
