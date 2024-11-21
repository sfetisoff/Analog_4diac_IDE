import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMenu, QMessageBox, QLabel, QPushButton
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import QRect, QLine, Qt, QPoint

from myblocks import BlockA, BlockB, BlockC, BlockD, MyBlock




class MyMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Рисование прямоугольника")
        self.setGeometry(100, 100, 800, 600)  # Установка размера окна
        self.list_blocks = []
        self.label = QLabel("Нажмите и двигайте мышь", self)
        self.label.setGeometry(50, 50, 300, 50)
        # Хранение координат для рисования
        self.current_x = 300
        self.current_y = 300
        self.drawing = False  # Состояние рисования
        self.connecting = False # Если True - выбран прямоугольник для связи
        self.all_lines = [] # Все линии связи
        self.current_line = None
        self.menu = self.menuBar().addMenu("Выбрать блок")
        self.setMouseTracking(True)
        self.rect_start_connect = None # Прямоугольник, из которого начали строить связь
        self.create_actions()

    def paintEvent(self, event):
        painter = QPainter(self)
        for block in self.list_blocks:
            painter.setBrush(QColor(block.color))
            for rect, text in zip(block.rectangles, block.labels):
                painter.drawRect(rect)
                text_rect = painter.boundingRect(rect, 0, text) # Добавляем подписи к прямоугольникам
                text_x = int(rect.x() + (rect.width() - text_rect.width()) / 2) # Центруем надпись в прямоугольнике
                text_y = int(rect.y() + (rect.height() - text_rect.height()) / 2)
                painter.drawText(text_x, text_y + text_rect.height(), text)

        pen = QPen(Qt.yellow, 3)
        for line in self.all_lines:
            painter.setPen(pen)  # Устанавливаем цвет линии
            painter.drawLine(line)



    def find_connection_rect(self):
        for block in self.list_blocks:
            for small_rect in block.rectangles[1:]:
                if small_rect.contains(self.current_x, self.current_y):
                    if self.connecting:
                        #print(self.rect_start_connect.parent.name, self.rect_start_connect.name)
                        small_rect.connect_lines.append(self.current_line)
                        self.rect_start_connect.connect_lines.append(self.current_line)
                        self.rect_start_connect.parent.connections[self.rect_start_connect.name].append((block.name, small_rect.name))
                        # Делаем, чтобы прямая приходила в центр прямоугольника
                        self.current_line.setP2(QPoint(small_rect.center().x(), small_rect.center().y()))
                    else:
                        self.connecting = True
                        self.rect_start_connect = small_rect
                        self.current_line = QLine(small_rect.center().x(), small_rect.center().y(),
                                                  self.current_x + 1, self.current_y + 1)
                        self.label.setText(f"Нажат {small_rect.name}")

                        self.all_lines.append(self.current_line)
                        self.update()

                    return True
        return False



    def find_rect(self): # Ищем прямоугольник, на который нажали
        for block in self.list_blocks:
            # rectangles[0], потому что там находится прямоугольник - основа блока
            if block.rectangles[0].contains(self.current_x, self.current_y):
                return block # Можем перемещать блок

    def mousePressEvent(self, event):
        self.current_x = event.x()
        self.current_y = event.y()
        self.drawing = True  # Установить состояние рисования
        self.label.setText(f"Нажато в ({self.current_x}, {self.current_y})")
        self.current_block = self.find_rect() # Проверка на нажатие на блок, который можно перемещать
        self.find_connection_rect()  # Проверка, выбрали ли мы один из входов/выходов для связей
        self.last_mouse_pos = event.pos()
        if self.current_block:
            self.current_block.change_coords(self.current_x, self.current_y)
            self.update()  # Запрос на перерисовку виджета


    def mouseReleaseEvent(self, event):
        self.current_block = None
        is_found = self.find_connection_rect()
        if (self.connecting == True) and (is_found == False):
            self.all_lines.pop(-1)
        self.current_line = None
        self.connecting = False # Сбросить построение связей
        self.drawing = False  # Сбросить состояние рисования
        x = event.x()
        y = event.y()
        self.label.setText(f"Отпущено в ({x}, {y})")
  # Запрос на перерисовку виджета
#

    def mouseMoveEvent(self, event):
        self.current_x = event.x()
        self.current_y = event.y()
        if self.drawing:  # Если кнопка мыши нажата
            self.label.setText(f"Движение нажатой мыши в ({self.current_x}, {self.current_y})")
            if self.current_block:
                self.current_block.change_coords(self.current_x, self.current_y)
            if self.current_line:
                self.current_line.setP2(QPoint(self.current_x, self.current_y))
        else:
            self.label.setText(f"Движение мыши в ({self.current_x}, {self.current_y})")

        self.last_mouse_pos = event.pos()
        self.update()  # Запрос на перерисовку виджета

    def create_actions(self):
        self.button = QPushButton('Показать словарь связей', self)
        self.button.setGeometry(50, 40, 200, 30)  # x, y, ширина, высота
        self.button.clicked.connect(self.show_connections)

        create_A_action = QAction("INT2INT", self)
        create_A_action.triggered.connect(self.create_block_A)

        create_B_action = QAction("OUT_ANY_CONSOLE", self)
        create_B_action.triggered.connect(self.create_block_B)

        create_C_action = QAction("Block_C", self)
        create_C_action.triggered.connect(self.create_block_C)

        create_D_action = QAction("Block_D", self)
        create_D_action.triggered.connect(self.create_block_D)

        self.menu.addAction(create_A_action)
        self.menu.addAction(create_B_action)
        self.menu.addAction(create_C_action)
        self.menu.addAction(create_D_action)

    def show_connections(self):
        for block in self.list_blocks:
            print(block.name, block.connections)

    def create_block_A(self): #INT2INT
        self.list_blocks.append(BlockA(self, 'INT2INT'))
        self.update()

    def create_block_B(self):
        self.list_blocks.append(BlockB(self, 'OUT_ANY_CONSOLE'))
        self.update()

    def create_block_C(self):
        self.list_blocks.append(BlockC(self))
        self.update()

    def create_block_D(self):
        self.list_blocks.append(BlockD(self))
        self.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MyMain()
    window.show()
    sys.exit(app.exec_())
