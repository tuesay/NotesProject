import sqlite3
import sys
import pyperclip

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QMenu, QInputDialog, \
    QListWidget

from noteEdit import NoteEdit
from mainUi import Ui_Notes


class Notes(QMainWindow, Ui_Notes):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.first_launch()

        self.initUi()

        self.list_update()
        self.tag_update()

    def first_launch(self):

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        try:
            cur.execute("""CREATE TABLE tags (
        tag_id   INTEGER PRIMARY KEY AUTOINCREMENT
                         UNIQUE
                         NOT NULL,
        tag_name TEXT    NOT NULL
                         UNIQUE
    );
    """)
            cur.execute("""CREATE TABLE notes (
        id      INTEGER PRIMARY KEY AUTOINCREMENT
                        UNIQUE
                        NOT NULL,
        name    TEXT    NOT NULL
                        UNIQUE,
        text    TEXT,
        img_data TEXT,
        tag_id  INTEGER REFERENCES tags (tag_id) 
    );
    """)
            con.commit()
        except sqlite3.OperationalError:
            pass
        con.close()

    def initUi(self):
        self.searchLine.textChanged.connect(self.list_update)
        self.sortBy.currentTextChanged.connect(self.list_update)
        self.tagSelect.currentIndexChanged.connect(self.list_update)

        self.noteList.doubleClicked.connect(self.note_redaction)

        self.noteList.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection)  # мультиселекция

        self.noteList.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)  # контекстное меню для QListWidget
        self.noteList.customContextMenuRequested.connect(
            self.show_list_context)

        self.tagSelect.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)  # контекстное меню для QComboBox
        self.tagSelect.customContextMenuRequested.connect(
            self.show_tag_context)

    def list_update(self):  # отвечает за сортировку и обновление списка заметок
        self.noteList.clear()

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        search = f'%{self.searchLine.text()}%'
        tag = self.tagSelect.currentText()

        if self.searchLine.text() == '':  # поиск по имени заметки
            if tag == 'Все':
                ids = cur.execute("SELECT id FROM notes").fetchall()
            else:
                ids = cur.execute(
                    "SELECT id FROM notes WHERE tag_id = "
                    "(SELECT tag_id FROM tags WHERE tag_name = ?)", (tag, )).fetchall()
        else:
            if tag == 'Все':
                ids = cur.execute(
                    "SELECT id FROM notes WHERE name LIKE ?", (search, )).fetchall()
            else:
                ids = cur.execute(
                    "SELECT id FROM notes WHERE name LIKE ? AND tag_id "
                    "= (SELECT tag_id FROM tags WHERE tag_name = ?)", (search, tag)).fetchall()

        if self.sortBy.currentText() == 'Алфавит':  # сортировка в алфавитном порядке
            self.noteList.setSortingEnabled(True)
        else:
            self.noteList.setSortingEnabled(False)

        for i in ids[::-1]:  # список перевернут в порядке последнего созданного
            name = cur.execute(
                "SELECT name FROM notes WHERE id = ?", (i[0], )).fetchone()[0]

            self.noteList.addItem(QListWidgetItem(f'{name}'))

        self.noteCount.setText(f'Количество заметок: {len(ids)}')

        con.close()

    def tag_update(self):  # обновляет теги в QComboBox
        self.tagSelect.clear()

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        self.tagSelect.addItem('Все')

        tags = cur.execute("SELECT tag_name FROM tags").fetchall()
        for i in tags:
            self.tagSelect.addItem(i[0])

        con.close()

    def duplicate_handle_tag(self, name):  # обрабатывает дубликаты имен для тегов
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

    def keyPressEvent(self, event):  # открытие заметки с помощью клавиши Enter
        if event.key() == Qt.Key.Key_Return and self.noteList.currentItem() is not None:
            self.note_redaction()

        elif event.key() == Qt.Key.Key_F1:
            pass

    # функция для обработки контекстного меню для QListWidget
    def show_list_context(self, pos):
        # положение относительно главного виджета
        global_pos = self.noteList.mapToGlobal(pos)
        index = self.noteList.indexAt(pos)  # проверка на выделения элемента

        if not index.isValid():  # элемент не выделен
            context_menu = QMenu()

            create = QAction('Создать заметку', self)
            create.triggered.connect(self.note_creation)

            context_menu.addAction(create)
            context_menu.exec(global_pos)

        else:  # элемент выделен
            name = self.noteList.currentItem().text()
            items = self.noteList.selectedItems()

            con = sqlite3.connect('note.sqlite')
            tag_id = con.cursor().execute(
                "SELECT tag_id FROM notes WHERE name = ?", (name, )).fetchone()[0]
            tag_name = con.cursor().execute(
                "SELECT tag_name FROM tags WHERE tag_id = ?", (tag_id, )).fetchone()
            con.close()

            context_menu = QMenu()

            if tag_name is not None:  # информация о теге заметки
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
            copy.triggered.connect(lambda: pyperclip.copy(self.noteList.currentItem().text()))
            tag_assign.triggered.connect(self.tag_assign)
            tag_unassign.triggered.connect(self.tag_unassign)

            if len(items) > 1:  # проверка на мультиселекцию
                delete = QAction('Удалить заметки', self)
                tag_assign = QAction('Присвоить заметкам тег')
                tag_unassign = QAction('Отсоединить заметки от тега', self)

                delete.triggered.connect(self.note_delete)
                tag_assign.triggered.connect(self.tag_assign)
                tag_unassign.triggered.connect(self.tag_unassign)
                context_menu.addActions([delete, tag_assign, tag_unassign])

            else:
                if tag_id is None:  # если тега нет, то к элементу можно только присвоить тег
                    context_menu.addAction(tag_name)
                    context_menu.addSeparator()
                    context_menu.addActions([edit, copy, tag_assign, delete])
                else:
                    context_menu.addAction(tag_name)
                    context_menu.addSeparator()
                    context_menu.addActions([edit, copy, tag_unassign, delete])
            context_menu.exec(global_pos)

    def show_tag_context(self, pos):  # контекстное меню для QComboBox
        global_pos = self.tagSelect.mapToGlobal(pos)

        context_menu = QMenu()

        create = QAction('Создать тег', self)
        delete = QAction('Удалить тег', self)

        create.triggered.connect(self.tag_creation)
        delete.triggered.connect(self.tag_delete)

        context_menu.addAction(create)
        context_menu.addAction(delete)

        context_menu.exec(global_pos)

    def tag_creation(self):
        name, ok_pressed = QInputDialog.getText(self, "Введите название тега",
                                                "Название тега:")

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        if ok_pressed:
            try:

                cur.execute("INSERT INTO tags(tag_name) VALUES(?)", (name,))

            except sqlite3.IntegrityError:
                # функция возвращает уникальное имя
                name = self.duplicate_handle_tag(name)

                cur.execute("INSERT INTO tags(tag_name) VALUES(?)", (name,))

        con.commit()
        con.close()
        self.tag_update()

    def tag_assign(self):
        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        tags = map(lambda x: x[0], cur.execute(
            "SELECT tag_name FROM tags").fetchall())

        # открывается диалоговое окно с QComboBox для выбора тега
        tag, ok_pressed = QInputDialog.getItem(
            self, 'Выбор тега', 'Выберите тег:', tags, editable=False)

        if ok_pressed:
            name = self.noteList.currentItem().text()
            items = self.noteList.selectedItems()
            if len(items) > 1:  # возможно присвоить тег к множеству элементов
                for name in items:
                    cur.execute(
                        "UPDATE notes SET tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?) "
                        "WHERE name = ?", (tag, name.text()))
            else:
                cur.execute(
                    "UPDATE notes SET tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?)"
                    " WHERE name = ?", (tag, name))
        con.commit()
        con.close()

    def tag_unassign(self):
        name = self.noteList.currentItem().text()
        items = self.noteList.selectedItems()

        con = sqlite3.connect('note.sqlite')
        cur = con.cursor()

        if len(items) > 1:  # возможно отсоединить элементы от тега(ов)
            for name in items:
                cur.execute(
                    "UPDATE notes SET tag_id = NULL WHERE name = ?", (name.text(),))

        else:
            cur.execute(
                "UPDATE notes SET tag_id = NULL WHERE name = ?", (name, ))

        con.commit()
        con.close()
        self.list_update()

    def tag_delete(self):
        # Удаление тега происходит когда пользователь выбирает определенный тег в QComboBox,
        # при открытии контекстного меню, выбранный тег удаляется
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

        if len(items) > 1:  # возможно удалить несколько элементов
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
        # Если заметка создается с уже выбранным тегом в QComboBox тег
        # автоматически присваивается созданной заметке
        if self.tagSelect.currentText() != 'Без тега':
            tag = self.tagSelect.currentText()
        else:
            tag = None
        print('creating a new note with a tag:', tag)  # лог
        dialog = NoteEdit(name=None, tag=tag)
        dialog.exec()

        self.list_update()
        self.tag_update()

        self.tagSelect.setCurrentText(dialog.tag_return())

    def note_redaction(self):
        name = self.noteList.currentItem().text()

        print(f'redacting: {name}')  # лог
        # для редактирования классу NoteEdit передается имя выбранной заметки
        dialog = NoteEdit(name)
        dialog.exec()

        self.list_update()
        self.tag_update()

        self.tagSelect.setCurrentText(dialog.note_save())


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Notes()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
