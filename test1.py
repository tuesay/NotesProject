import sys
from PyQt6.QtWidgets import QApplication, QWidget, QMenu, QListWidget, QVBoxLayout
from PyQt6.QtCore import Qt

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Insert Context Menu to ListWidget')
        self.window_width, self.window_height = 800, 600
        self.setMinimumSize(self.window_width, self.window_height)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.listWidget = QListWidget()
        self.listWidget.addItems(['Facebook', 'Microsoft', 'Google'])
        layout.addWidget(self.listWidget)

        # Настройка политики контекстного меню
        self.listWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.listWidget.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        # Определяем позицию курсора
        global_pos = self.listWidget.mapToGlobal(pos)

        # Проверяем, есть ли элемент под курсором
        index = self.listWidget.indexAt(pos)
        if not index.isValid():
            return

        # Создаем контекстное меню
        menu = QMenu()
        menu.addAction('Action 1')
        menu.addAction('Action 2')
        menu.addAction('Action 3')

        # Выполнение действия после выбора пункта меню
        action = menu.exec(global_pos)
        if action:
            item = self.listWidget.itemFromIndex(index)
            print(f'Selected item: {item.text()}')  # Выводим текст выбранного элемента

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())