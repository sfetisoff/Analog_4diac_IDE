import sys
from importlib.resources import Resource

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMenu, QMessageBox, QLabel, QPushButton, QLineEdit
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import QRect, QLine, Qt, QPoint
import xml.etree.ElementTree as ET

import easygui

from myblocks import BlockA, BlockB, BlockC, BlockD, MyBlock, BlockStart
from xml_saving import create_xml



class MyMain(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Analog 4diac")
        self.setGeometry(100, 100, 800, 600)  # Установка размера окна
        self.list_blocks = [] # Список со всеми блоками
        self.block_start = None
        self.label = QLabel("Нажмите и двигайте мышь", self)
        self.label.setGeometry(50, 50, 300, 50)
        # Хранение координат для рисования
        self.current_x = 300
        self.current_y = 300
        self.coords_coef = 4 # Масштабирование координат для совместимости с 4diac
        self.drawing = False  # Состояние рисования
        self.connecting = False # Если True - выбран прямоугольник для связи
        self.all_lines = [] # Все линии связи
        self.current_line = None
        self.menu_file = self.menuBar().addMenu("File")
        self.menu_blocks = self.menuBar().addMenu("Select a block")
        self.setMouseTracking(True)
        self.rect_start_connect = None # Прямоугольник, из которого начали строить связь
        self.count_blocks = {'Block_A': 1, 'Block_B': 1, 'Block_C': 1, 'Block_D': 1}
        self.create_block_dict = {'E_RESTART': BlockStart,
                                  'INT2INT': BlockA,
                                  'OUT_ANY_CONSOLE': BlockB}

        self.create_actions()


    def update_all(self):
        self.update()
        self.update_block_names()

    def paintEvent(self, event):
        painter = QPainter(self)
        for block in self.list_blocks:
            painter.setBrush(QColor(block.color))
            for rect in block.rectangles:
                painter.drawRect(rect) # Рисуем блок
                painter.drawText(rect, Qt.AlignCenter, rect.name) # Рисуем центрированный тип элемента(CNF, IN ...)

        pen = QPen(Qt.yellow, 3)
        for line in self.all_lines:
            painter.setPen(pen)  # Устанавливаем цвет линии
            painter.drawLine(line)


    def update_block_names(self):
        for block in self.list_blocks:
            name_x = int(block.x + (block.width - block.name_label.width()) / 2)  # Центруем надпись в прямоугольнике
            name_y = block.y - block.height // 4
            block.name_label.move(name_x, name_y)
            block.name_edit.move(name_x, name_y)
            block.name_label.show()

    def on_label_click(self, event, block):
        # При нажатии на метку скрываем метку и показываем поле ввода
        block.name_edit.setText(block.name_label.text())
        block.name_edit.setVisible(True)
        block.name_edit.setFocus()
        # Подключаем сигнал для завершения редактирования
        try:
            block.name_edit.returnPressed.disconnect()
        except:
            pass
        block.name_edit.returnPressed.connect(lambda: self.on_edit_finished(block))
        # Скрываем метку
        block.name_label.setVisible(False)

    def on_edit_finished(self, block):
        # При завершении редактирования обновляем текст метки и скрываем поле ввода
        block.name_label.setText(block.name_edit.text())
        block.name = block.name_edit.text() # Обновляем block.name
        block.name_label.setVisible(True)
        block.name_edit.setVisible(False)


    def find_connection_rect(self):
        for block in self.list_blocks:
            for small_rect in block.rectangles[1:]:
                if small_rect.contains(self.current_x, self.current_y):
                    if self.connecting:
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
                        self.update_all()

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
            self.update_all()  # Запрос на перерисовку виджета


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
        self.update_all()  # Запрос на перерисовку виджета

    def create_actions(self):
        self.button = QPushButton('Показать словарь связей', self)
        self.button.setGeometry(50, 40, 200, 30)  # x, y, ширина, высота
        self.button.clicked.connect(self.show_connections)

        create_Start_action = QAction("START", self)
        create_Start_action.triggered.connect(self.create_block_Start)

        create_A_action = QAction("INT2INT", self)
        create_A_action.triggered.connect(self.create_block_A)

        create_B_action = QAction("OUT_ANY_CONSOLE", self)
        create_B_action.triggered.connect(self.create_block_B)

        create_C_action = QAction("Block_C", self)
        create_C_action.triggered.connect(self.create_block_C)

        create_D_action = QAction("Block_D", self)
        create_D_action.triggered.connect(self.create_block_D)

        self.menu_blocks.addAction(create_Start_action)
        self.menu_blocks.addAction(create_A_action)
        self.menu_blocks.addAction(create_B_action)
        self.menu_blocks.addAction(create_C_action)
        self.menu_blocks.addAction(create_D_action)

        open_project_action = QAction("Open", self)
        open_project_action.triggered.connect(self.read_xml)

        create_xml_action = QAction("Save as XML", self)
        create_xml_action.triggered.connect(lambda: create_xml(self.list_blocks, self.block_start, self.coords_coef))

        self.menu_file.addAction(open_project_action)
        self.menu_file.addAction(create_xml_action)

    def show_connections(self):
        for block in self.list_blocks:
            print(block.name, block.connections)
            for source_element, ar_elements in block.connections.items():
                if ar_elements:
                    for dest_block_name, dest_el in ar_elements:
                        print(f"Connection Source = {block.name}.{source_element},"
                              f"Destination = {dest_block_name}.{dest_el}, Comment = ")

    def create_block_Start(self):
        self.block_start = BlockStart(self, 'START')
        self.list_blocks.append(self.block_start)
        self.update_all()

    def create_block_A(self): #INT2INT
        k_blocks = self.count_blocks['Block_A'] # Сколько блоков такого типа уже есть
        self.list_blocks.append(BlockA(self, f'INT2INT_{k_blocks}'))
        self.count_blocks['Block_A'] += 1
        self.update_all()


    def create_block_B(self):
        k_blocks = self.count_blocks['Block_B']  # Сколько блоков такого типа уже есть
        self.list_blocks.append(BlockB(self, f'OUT_ANY_CONSOLE_{k_blocks}'))
        self.count_blocks['Block_B'] += 1
        self.update_all()

    def create_block_C(self):
        self.list_blocks.append(BlockC(self))
        self.update_all()

    def create_block_D(self):
        self.list_blocks.append(BlockD(self))
        self.update_all()

    def contextMenuEvent(self, event):
        for block in self.list_blocks:
            # rectangles[0], потому что там находится прямоугольник - основа блока
            if block.rectangles[0].contains(self.current_x, self.current_y):
                context_menu = QMenu(self)

                # Добавляем действия в контекстное меню
                action1 = QAction("Удалить", self)
                action1.triggered.connect(lambda: self.delete_block(block))
                context_menu.addAction(action1)

                # Отображаем контекстное меню
                context_menu.exec_(event.globalPos())
        self.update_all()


    def delete_block(self, block):
        self.list_blocks.remove(block)
        block.name_edit.deleteLater()
        block.name_label.deleteLater()

    def create_connections(self, connections):
        for connection in connections.findall('Connection'):
            source = connection.get('Source')
            destination = connection.get('Destination')
            name_source, source_element = source.split('.')
            name_dest, dest_element = destination.split('.')

            for block in self.list_blocks:
                if block.name == name_source:
                    for rect in block.rectangles[1:]:
                        if rect.name == source_element:
                            self.rect_start_connect = rect
                if block.name == name_dest:
                    for rect in block.rectangles[1:]:
                        if rect.name == dest_element:
                            dest_rect = rect

            self.current_line = QLine(self.rect_start_connect.center().x(), self.rect_start_connect.center().y(),
                                      dest_rect.center().x(), dest_rect.center().y())
            dest_rect.connect_lines.append(self.current_line)
            self.rect_start_connect.connect_lines.append(self.current_line)
            self.rect_start_connect.parent.connections[self.rect_start_connect.name].append(
                (dest_rect.parent.name, dest_rect.name))
            self.all_lines.append(self.current_line)
            self.current_line = None



    def read_xml(self):
        try:
            input_file = easygui.fileopenbox(filetypes=["*.xml"])
            tree = ET.parse(input_file)
            root = tree.getroot()
            device = root.find('Device')
            resource = device.find('Resource')
            fb_network = resource.find('FBNetwork')
            self.create_block_Start()

            for fb in fb_network.findall('FB'): # Создаём FB
                name = fb.get('Name')
                block_type = fb.get('Type')
                x = int(fb.get('x')) // self.coords_coef
                y = int(fb.get('y')) // self.coords_coef

                self.list_blocks.append(self.create_block_dict[block_type](self, name=name, x=x, y=y))

            event_connections = fb_network.find('EventConnections')
            data_connections = fb_network.find('DataConnections')
            self.create_connections(event_connections)
            self.create_connections(data_connections)
            self.update_all()
        except:
            print("File reading error")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MyMain()
    window.show()
    sys.exit(app.exec_())
