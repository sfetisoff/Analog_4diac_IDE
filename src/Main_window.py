import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMenu, QMessageBox, QLabel, QPushButton, QLineEdit
from PyQt5.QtGui import QPainter, QColor, QPen, QCursor, QFont
from PyQt5.QtCore import QRect, QLine, Qt, QPoint
import xml.etree.ElementTree as ET

import easygui

from myblocks import BlockA, BlockB, BlockC, BlockD, MyBlock, BlockStart
from xml_saving import create_xml, create_fboot
from smart_connections import Connection


class MyMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analog 4diac")
        self.setGeometry(100, 100, 800, 600)  # Установка размера окна
        self.list_blocks = []  # Список со всеми блоками
        self.block_start = None
        self.label = QLabel("Нажмите и двигайте мышь", self)
        self.label.setGeometry(50, 50, 300, 50)
        # Хранение координат для рисования
        self.current_x = 300
        self.current_y = 300
        self.coords_coef = 6  # Масштабирование координат для совместимости с 4diac
        self.pressed = False  # Состояние рисования
        self.connecting = False  # Если True - выбран прямоугольник для связи
        self.all_lines = []  # Все линии связи
        self.current_line = None
        self.menu_file = self.menuBar().addMenu("File")
        self.menu_blocks = self.menuBar().addMenu("Select a block")
        self.setMouseTracking(True)
        self.rect_start_connect = None  # Прямоугольник, из которого начали строить связь
        self.count_blocks = {'Block_A': 1, 'Block_B': 1, 'Block_C': 1, 'Block_D': 1}
        self.create_block_dict = {'E_RESTART': BlockStart,
                                  'INT2INT': BlockA,
                                  'OUT_ANY_CONSOLE': BlockB,
                                  'STRING2STRING': BlockC,
                                  'F_ADD': BlockD}
        self.polylines_array = []
        self.moving_lines = False
        self.movable_polyline = None
        self.drawing_connection = False
        self.create_actions()

    def update_all(self):
        self.update()
        self.update_block_names()
        self.update_rect_values()

    def paintEvent(self, event):
        painter = QPainter(self)
        for block in self.list_blocks:
            painter.setBrush(QColor(block.color))
            for rect in block.rectangles:
                painter.drawRect(rect)  # Рисуем блок
                font = QFont("Arial", 8)
                painter.setFont(font)
                painter.drawText(rect, Qt.AlignCenter, rect.name)  # Рисуем центрированный тип элемента(CNF, IN ...)

        pen1 = QPen(Qt.red, 1)
        pen2 = QPen(Qt.blue, 1)
        painter.setPen(pen1)
        for polyline in self.polylines_array:
            if polyline.color == 'red':
                painter.setPen(pen1)
            else:
                painter.setPen(pen2)
            for line in polyline.line_array:
                painter.drawLine(line)
            painter.drawPolygon(polyline.triangle)

    def update_rect_values(self):
        for block in self.list_blocks:
            for rect in block.rectangles:
                if rect.editable_label:
                    rect.value_x = rect.x() - rect.value_width
                    rect.value_y = rect.y() + (rect.height() - rect.value_height) // 2
                    rect.editable_label.move(rect.value_x, rect.value_y)

    def update_block_names(self):
        for block in self.list_blocks:
            name_x = block.x + (block.width - block.label_width) // 2  # Центруем надпись в прямоугольнике
            name_y = block.y - 25
            block.editable_label.move(name_x, name_y)

    def find_block(self):  # Ищем прямоугольник, на который нажали
        for block in self.list_blocks:
            # rectangles[0], потому что там находится прямоугольник - основа блока
            if block.rectangles[0].contains(self.current_x, self.current_y):
                return block  # Можем перемещать блок

    def find_connect_element(self, is_left_flag):
        for block in self.list_blocks:
            for rect in block.rectangles[1:]:
                if rect.contains(self.current_x, self.current_y) and (rect.is_left is is_left_flag):
                    return rect

    def mousePressEvent(self, event):
        self.current_x = event.x()
        self.current_y = event.y()
        self.last_mouse_pos = event.pos()
        self.label.setText(f"Нажато в ({self.current_x}, {self.current_y})")

        self.movable_polyline, self.coord = self.check_moving_connect(event)  # Проверка нажали ли мы на соединение
        # self.find_connection_rect()  # Проверка, выбрали ли мы один из входов/выходов для связей
        self.source_element = self.find_connect_element(is_left_flag=False)

        if self.movable_polyline is None:
            self.current_block = self.find_block()  # Проверка на нажатие на блок, который можно перемещать
            if self.current_block:
                self.current_block.change_coords(self.current_x, self.current_y)
                self.update_all()  # Запрос на перерисовку виджета
            elif self.source_element:  # Проверка, выбрали ли мы один из входов/выходов для связей
                self.current_connection = Connection(QPoint(self.source_element.right() + 1,
                                                            self.source_element.center().y()),
                                                     QPoint(self.current_x + 1,
                                                            self.current_y + 2))
                self.polylines_array.append(self.current_connection)
                self.drawing_connection = True
        self.pressed = True  # Установить состояние нажатия

    def mouseReleaseEvent(self, event):
        self.current_x = event.x()
        self.current_y = event.y()
        if self.drawing_connection:
            self.destination_element = self.find_connect_element(is_left_flag=True)
            if self.destination_element:
                if self.current_connection.simple:
                    self.current_connection.simple_case(dx1=self.current_connection.dx1,
                                                        destination=QPoint(self.destination_element.left() - 1,
                                                                           self.destination_element.center().y()))
                else:
                    self.current_connection.hard_case(dx1=self.current_connection.dx1,
                                                      dx2=self.current_connection.dx2,
                                                      dy1=self.current_connection.dy1,
                                                      destination=QPoint(self.destination_element.left() - 1,
                                                                         self.destination_element.center().y()))
                self.source_element.parent.connections[self.source_element.name].append(
                    (self.destination_element.parent.name, self.destination_element.name))
                if (self.source_element.data_element or self.destination_element.data_element):
                    self.current_connection.color = 'blue'
                self.source_element.connect_lines.append(self.current_connection)
                self.destination_element.connect_lines.append(self.current_connection)
            else:
                self.polylines_array.pop(-1)

        self.current_block = None
        self.current_connection = None
        self.drawing_connection = False  # Сбросить построение связей
        self.pressed = False  # Сбросить состояние нажатия
        self.movable_polyline = None
        x = event.x()
        y = event.y()
        self.label.setText(f"Отпущено в ({x}, {y})")
        self.update()

    def mouseMoveEvent(self, event):
        self.current_x = event.x()
        self.current_y = event.y()
        if self.pressed:  # Если кнопка мыши нажата
            self.label.setText(f"Движение нажатой мыши в ({self.current_x}, {self.current_y})")
            if self.current_block:  # Если выбран блок для перемещения
                self.current_block.change_coords(self.current_x, self.current_y)
            elif self.drawing_connection:  # Если мы рисуем новую связь
                self.current_connection.change_coords(event)
            else:
                self.change_movable_connection(event)
        else:
            self.label.setText(f"Движение мыши в ({self.current_x}, {self.current_y})")
            self.check_moving_connect(event)

        self.last_mouse_pos = event.pos()
        self.update_all()  # Запрос на перерисовку виджета

    def change_movable_connection(self, event):
        if self.movable_polyline:
            if self.movable_polyline.simple:
                if (event.x() - self.movable_polyline.x1 > 10) and (self.movable_polyline.x3 - event.x() > 10):
                    self.movable_polyline.simple_case(dx1=event.x() - self.movable_polyline.x1)
            else:
                if (self.coord == 'dx1') and (event.x() - self.movable_polyline.x1 > 10):
                    self.movable_polyline.hard_case(dx1=event.x() - self.movable_polyline.x1,
                                                    dx2=self.movable_polyline.dx2,
                                                    dy1=self.movable_polyline.dy1)
                elif self.coord == 'dy1':
                    self.movable_polyline.hard_case(dx1=self.movable_polyline.dx1,
                                                    dx2=self.movable_polyline.dx2,
                                                    dy1=self.movable_polyline.y1 - event.y())
                elif (self.coord == 'dx2') and (self.movable_polyline.x4 - event.x() > 10):
                    self.movable_polyline.hard_case(dx1=self.movable_polyline.dx1,
                                                    dx2=self.movable_polyline.x4 - event.x(),
                                                    dy1=self.movable_polyline.dy1)

    def check_moving_connect(self, event):
        for polyline in self.polylines_array:
            if polyline.rect_line2.contains(event.x(), event.y()):
                self.setCursor(QCursor(Qt.SizeHorCursor))
                return (polyline, 'dx1')
            elif polyline.rect_line3.contains(event.x(), event.y()):
                self.setCursor(QCursor(Qt.SizeVerCursor))
                return (polyline, 'dy1')
            elif polyline.rect_line4.contains(event.x(), event.y()):
                self.setCursor(QCursor(Qt.SizeHorCursor))
                return (polyline, 'dx2')
            else:
                self.unsetCursor()
        return (None, None)

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

        create_C_action = QAction("STRING2STRING", self)
        create_C_action.triggered.connect(self.create_block_C)

        create_D_action = QAction("F_ADD", self)
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

        create_fboot_action = QAction("Create fboot file", self)
        create_fboot_action.triggered.connect(lambda: create_fboot(self.list_blocks, self.block_start))

        self.menu_file.addAction(open_project_action)
        self.menu_file.addAction(create_xml_action)
        self.menu_file.addAction(create_fboot_action)

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

    def create_block_A(self):  # INT2INT
        k_blocks = self.count_blocks['Block_A']  # Сколько блоков такого типа уже есть
        self.list_blocks.append(BlockA(self, f'INT2INT_{k_blocks}'))
        self.count_blocks['Block_A'] += 1
        self.update_all()

    def create_block_B(self):
        k_blocks = self.count_blocks['Block_B']  # Сколько блоков такого типа уже есть
        self.list_blocks.append(BlockB(self, f'OUT_ANY_CONSOLE_{k_blocks}'))
        self.count_blocks['Block_B'] += 1
        self.update_all()

    def create_block_C(self):
        k_blocks = self.count_blocks['Block_C']
        self.list_blocks.append(BlockC(self, f'STRING2STRING_{k_blocks}'))
        self.count_blocks['Block_C'] += 1
        self.update_all()

    def create_block_D(self):
        k_blocks = self.count_blocks['Block_D']
        self.list_blocks.append(BlockD(self, f'F_ADD_{k_blocks}'))
        self.count_blocks['Block_D'] += 1
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
        block.editable_label.delete()
        for rect in block.rectangles:
            if rect.editable_label:
                rect.editable_label.delete()
        # block.name_label.deleteLater()

    def create_connections(self, connections):
        for connection in connections.findall('Connection'):
            source = connection.get('Source')
            destination = connection.get('Destination')
            name_source, source_element = source.split('.')
            name_dest, dest_element = destination.split('.')
            dx1 = connection.get('dx1')
            dx2 = connection.get('dx2')
            dy1 = connection.get('dy')
            if dx1:
                dx1 = int(float(dx1) / self.coords_coef)
            if dx2:
                dx2 = int(float(dx2) / self.coords_coef)
            if dy1:
                dy1 = int(float(dy1) / self.coords_coef)

            for block in self.list_blocks:
                if block.name == name_source:
                    for rect in block.rectangles[1:]:
                        if rect.name == source_element:
                            self.source_element = rect
                if block.name == name_dest:
                    for rect in block.rectangles[1:]:
                        if rect.name == dest_element:
                            self.destination_element = rect

            self.current_connection = Connection(
                QPoint(self.source_element.right() + 1, self.source_element.center().y()),
                QPoint(self.destination_element.left() - 1, self.destination_element.center().y()))
            if self.current_connection.simple:
                self.current_connection.simple_case(dx1=dx1)
            else:
                self.current_connection.hard_case(dx1=dx1, dx2=dx2, dy1=dy1)
            self.destination_element.connect_lines.append(self.current_connection)
            self.source_element.connect_lines.append(self.current_connection)
            self.source_element.parent.connections[self.source_element.name].append(
                (self.destination_element.parent.name, self.destination_element.name))
            self.polylines_array.append(self.current_connection)
            self.current_connections = None

    def read_xml(self):
        try:
            input_file = easygui.fileopenbox(filetypes=["*.xml"])
            tree = ET.parse(input_file)
            root = tree.getroot()
            device = root.find('Device')
            resource = device.find('Resource')
            fb_network = resource.find('FBNetwork')
            self.create_block_Start()

            for fb in fb_network.findall('FB'):  # Создаём FB
                name = fb.get('Name')
                block_type = fb.get('Type')
                x = int(float(fb.get('x')) / self.coords_coef)
                y = int(float(fb.get('y')) / self.coords_coef)
                current_fb = self.create_block_dict[block_type](self, name=name, x=x, y=y)
                self.list_blocks.append(current_fb)
                for parameter in fb.findall('Parameter'):
                    name = parameter.get('Name')
                    value = parameter.get('Value')
                    for rect in current_fb.rectangles:
                        if rect.editable_label:
                            if rect.name == name:
                                rect.value = value
                                rect.editable_label.label.setText(rect.value)

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
