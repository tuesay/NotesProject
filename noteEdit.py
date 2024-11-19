import sqlite3
import pyperclip

from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QAction, QPixmap

from noteEditUi import Ui_noteEdit

from PyQt6.QtWidgets import QDialog, QMenu, QInputDialog, QFileDialog


class NoteEdit(QDialog, Ui_noteEdit):
    def __init__(self, name=None, tag=None):
        super().__init__()

        self.name = name
        self.tag = tag

        self.setupUi(self)

        self.initUi()

        self.image_setup()

    def initUi(self):

        self.showImgPlace.clicked.connect(self.show_place)
        self.imageAdd.clicked.connect(self.img_add)
        self.imageDel.clicked.connect(self.img_del)
        self.noteSave.clicked.connect(self.note_save)
        self.noteCancel.clicked.connect(self.note_cancel)

        self.noteText.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.noteText.customContextMenuRequested.connect(self.show_text_context)

        self.tagSet.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.tagSet.customContextMenuRequested.connect(self.show_tag_context)

        self.imageAdd.hide()
        self.imageDisplay.hide()
        self.imageDel.hide()

        self.update_data()

    def update_data(self):
        # Функция отвечает за обновление данных уже существующей заметки и
        # обновление существующих тегов в QComboBox из БД
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

    def show_text_context(self, pos):
        global_pos = self.noteText.mapToGlobal(pos)

        self.textcur = self.noteText.textCursor()

        context_menu = QMenu()

        cut = QAction('Вырезать выделенный текст', self)
        copy = QAction('Копировать выделенный текст', self)
        delete = QAction('Удалить выделенный текст', self)
        clear = QAction('Удалить всё', self)

        cut.triggered.connect(lambda: (pyperclip.copy(self.textcur.selectedText()), self.textcur.removeSelectedText()))
        copy.triggered.connect(lambda: pyperclip.copy(self.textcur.selectedText()))
        delete.triggered.connect(lambda: self.textcur.removeSelectedText())
        clear.triggered.connect(lambda: self.noteText.clear())

        if self.textcur.hasSelection():

            context_menu.addAction(cut)
            context_menu.addAction(copy)
            context_menu.addSeparator()
            context_menu.addAction(delete)
            context_menu.addAction(clear)

        else:
            copy = QAction('Копировать всё')
            copy.triggered.connect(lambda: pyperclip.copy(self.textcur.selectedText()))

            context_menu.addAction(copy)
            context_menu.addSeparator()
            context_menu.addAction(clear)

        context_menu.exec(global_pos)

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
            self.imageDel.show()

            self.showImgPlace.setText('<<<')

        elif self.showImgPlace.text() == '<<<':

            self.imageAdd.hide()
            self.imageDisplay.hide()
            self.imageDel.hide()

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
                    "INSERT INTO notes(name, text, img_data, tag_id) "
                    "VALUES(?, ?, ?, (SELECT tag_id FROM tags WHERE tag_name = ?))", (name, text,
                                                                                      self.img_data, tag))

                con.commit()
                con.close()
            except sqlite3.IntegrityError:
                name = self.duplicate_handle_notes(name)
                cur.execute(
                    "INSERT INTO notes(name, text, img_data, tag_id) "
                    "VALUES(?, ?, ?, (SELECT tag_id FROM tags WHERE tag_name = ?))", (name, text,
                                                                                      self.img_data, tag))

                con.commit()
                con.close()
        else:
            try:
                cur.execute(
                    "UPDATE notes SET name = ?, text = ?, img_data = ?, "
                    "tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?) WHERE name = ?",
                    (name,
                     text,
                     self.img_data,
                     tag,
                     self.name))

                con.commit()
                con.close()
            except sqlite3.IntegrityError:
                name = self.duplicate_handle_notes(name)

                cur.execute(
                    "UPDATE notes SET name = ?, text = ?, img_data = ?, "
                    "tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?)"
                    " WHERE name = ?", (name, text, self.img_data, tag, self.name))

                con.commit()
                con.close()

        self.close()
        print(f'saved note: {name} with tag: {tag}')

    def tag_return(self):
        return self.tag

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

    def image_setup(self):

        if self.name is not None:
            con = sqlite3.connect('note.sqlite')
            cur = con.cursor()

            image_data = cur.execute("SELECT img_data FROM notes WHERE name = ?",
                                            (self.name,)).fetchone()

            if image_data[0] is not None:
                self.img_data = image_data[0]

                self.showImgPlace.setText('<<<')

                self.img_display()

            else:
                self.img_data = None

            con.close()

    def img_add(self):
        try:
            img = QFileDialog.getOpenFileName(self, 'Добавить изображение', '',
                                              'Изображение (*.jpg);;Изображение (*.png)')[0]
        except FileNotFoundError:
            print('file not exist')

        with open(img, 'rb') as f:
            self.img_data = f.read()
            self.img_display()

    def img_del(self):
        self.imageDisplay.clear()

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()
        try:
            cur.execute("UPDATE notes SET image_data = ?", (None, ))
        except sqlite3.OperationalError:
            pass

        con.commit()
        con.close()

    def img_display(self):
        pixmap = QPixmap()

        img_data_qbyte = QByteArray(bytes(self.img_data))

        pixmap.loadFromData(img_data_qbyte)

        pixmap = pixmap.scaled(int(pixmap.width() * 0.2), int(pixmap.height() * 0.2),
                               Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.imageDisplay.show()
        self.imageAdd.show()
        self.imageDel.show()

        self.imageDisplay.setScaledContents(False)
        self.imageDisplay.setFixedSize(pixmap.width(), pixmap.height())
        self.imageDisplay.setPixmap(pixmap)

