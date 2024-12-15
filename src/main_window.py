import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMenu, QLabel
from PyQt5.QtGui import QPainter, QColor, QPen, QCursor, QFont, QBrush
from PyQt5.QtCore import Qt, QPoint

import custom_blocks as cb
from saving import create_xml, create_fboot
from smart_connections import Connection
from fbt_sending import TcpFileSender
import loading

class MyMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analog 4diac")
        self.setGeometry(100, 100, 800, 600)  # Установка размера окна
        self.list_blocks = []  # Список со всеми блоками
        self.block_start = None
        self.file_path = '../project_files/project1.xml'
        self.label = QLabel("Нажмите и двигайте мышь", self)
        self.label.setGeometry(10, 10, 300, 50)
        # Хранение координат для рисования
        self.current_x = 300
        self.current_y = 300
        self.coords_coef = 5  # Масштабирование координат для совместимости с 4diac
        self.pressed = False  # Состояние нажатия
        self.current_block = None
        self.menu_file = self.menuBar().addMenu("File")
        self.menu_blocks = self.menuBar().addMenu("Select a block")
        self.menu_run = self.menuBar().addMenu('Run')
        self.setMouseTracking(True)
        self.source_element = None  # Прямоугольник, из которого начали строить связь
        self.destination_element = None
        self.count_blocks = cb.count_blocks()

        self.create_block_dict = cb.all_block_classes()
        self.polylines_list = []
        self.movable_polyline = None
        self.drawing_connection = False
        self.create_actions()

    def update_all(self):
        self.update()
        self.update_block_names()
        self.update_rect_values()

    def paintEvent(self, event):
        painter = QPainter(self)
        font = QFont("Arial", 7)
        painter.setFont(font)
        for block in self.list_blocks:
            painter.setBrush(QColor(block.color))
            for rect in block.rectangles:
                painter.drawRect(rect)  # Рисуем блок
                painter.drawText(rect, Qt.AlignCenter, rect.name)  # Рисуем центрированный тип элемента(CNF, IN ...)

        pen1 = QPen(Qt.red, 1)
        pen2 = QPen(Qt.blue, 1)
        pen3 = QPen(Qt.black, 1)
        brush1 = QBrush(Qt.red)
        brush2 = QBrush(Qt.blue)
        brush3 = QBrush(Qt.black)

        for polyline in self.polylines_list:
            if polyline.color == 'red':
                painter.setPen(pen1)
                painter.setBrush(brush1)
            elif polyline.color == 'blue':
                painter.setPen(pen2)
                painter.setBrush(brush2)
            else:
                painter.setPen(pen3)
                painter.setBrush(brush3)
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

        self.source_element = self.find_connect_element(is_left_flag=False)

        if self.movable_polyline is None:
            self.current_block = self.find_block()  # Проверка на нажатие на блок, который можно перемещать
            if self.current_block:
                self.current_block.change_coords(self.current_x, self.current_y)

            elif self.source_element:  # Проверка, выбрали ли мы один из входов/выходов для связей
                self.current_connection = Connection(QPoint(self.source_element.right() + 1,
                                                            self.source_element.center().y()),
                                                     QPoint(self.current_x + 1,
                                                            self.current_y + 2))

                self.polylines_list.append(self.current_connection)
                self.drawing_connection = True
        self.pressed = True  # Установить состояние нажатия
        self.update_all()  # Запрос на перерисовку виджета

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
                else:
                    self.current_connection.color = 'red'
                self.source_element.connect_lines.append(self.current_connection)
                self.destination_element.connect_lines.append(self.current_connection)
            else:
                self.polylines_list.pop(-1)

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
                                                    dy1=event.y() - self.movable_polyline.y1 )
                elif (self.coord == 'dx2') and (self.movable_polyline.x4 - event.x() > 10):
                    self.movable_polyline.hard_case(dx1=self.movable_polyline.dx1,
                                                    dx2=self.movable_polyline.x4 - event.x(),
                                                    dy1=self.movable_polyline.dy1)

    def check_moving_connect(self, event):
        for polyline in self.polylines_list:
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

        create_Start_action = QAction("START", self)
        create_Start_action.triggered.connect(lambda: cb.create_block_Start(self))

        create_A_action = QAction("INT2INT", self)
        create_A_action.triggered.connect(lambda: cb.create_block_A(self))

        create_B_action = QAction("OUT_ANY_CONSOLE", self)
        create_B_action.triggered.connect(lambda: cb.create_block_B(self))

        create_C_action = QAction("STRING2STRING", self)
        create_C_action.triggered.connect(lambda: cb.create_block_C(self))

        create_D_action = QAction("F_ADD", self)
        create_D_action.triggered.connect(lambda: cb.create_block_D(self))

        self.menu_blocks.addAction(create_Start_action)
        self.menu_blocks.addAction(create_A_action)
        self.menu_blocks.addAction(create_B_action)
        self.menu_blocks.addAction(create_C_action)
        self.menu_blocks.addAction(create_D_action)

        open_project_action = QAction("Open", self)
        open_project_action.triggered.connect(lambda: loading.read_xml(self))

        save_action = QAction("Save", self)
        save_action.triggered.connect(lambda: create_xml(self.list_blocks, self.block_start,
                                                         self.coords_coef, with_gui=False,
                                                         old_file_path=self.file_path))

        create_xml_action = QAction("Save as XML", self)
        create_xml_action.triggered.connect(lambda: create_xml(self.list_blocks, self.block_start, self.coords_coef))

        create_fboot_action = QAction("Create fboot file", self)
        create_fboot_action.triggered.connect(lambda: create_fboot(self.list_blocks, self.block_start))

        self.menu_file.addAction(open_project_action)
        self.menu_file.addAction(save_action)
        self.menu_file.addAction(create_xml_action)
        self.menu_file.addAction(create_fboot_action)

        deploy_action = QAction('Deploy', self)
        deploy_action.triggered.connect(self.deploy)
        self.menu_run.addAction(deploy_action)

    def deploy(self):
        create_fboot(self.list_blocks, self.block_start, with_gui=False)
        TcpFileSender('../project_files/deploy.fboot')

    def show_connections(self):
        for block in self.list_blocks:
            print(block.name, block.connections)
            for source_element, ar_elements in block.connections.items():
                if ar_elements:
                    for dest_block_name, dest_el in ar_elements:
                        print(f"Connection Source = {block.name}.{source_element},"
                              f"Destination = {dest_block_name}.{dest_el}, Comment = ")



    def contextMenuEvent(self, event):
        cur_polyline, text = self.check_moving_connect(event)
        if cur_polyline:
            line_context_menu = QMenu(self)
            action = QAction("Delete connection", self)
            action.triggered.connect(lambda: self.delete_connection(cur_polyline))
            line_context_menu.addAction(action)
            line_context_menu.exec_(event.globalPos())
        else:
            for block in self.list_blocks:
                # rectangles[0], потому что там находится прямоугольник - основа блока
                if block.rectangles[0].contains(self.current_x, self.current_y):
                    context_menu = QMenu(self)

                    # Добавляем действия в контекстное меню
                    action1 = QAction("Delete block", self)
                    action1.triggered.connect(lambda: self.delete_block(block))
                    context_menu.addAction(action1)

                    # Отображаем контекстное меню
                    context_menu.exec_(event.globalPos())
        self.update_all()

    def clear(self):
        while self.list_blocks:
            self.delete_block(self.list_blocks[0])
        self.polylines_list = []
        self.list_blocks = []
        self.pressed = False
        self.update_all()

    def delete_block(self, block):
        for rect in block.rectangles:
            if rect.editable_label:
                rect.editable_label.delete()
            while rect.connect_lines:
                self.delete_connection(rect.connect_lines[0])

        self.list_blocks.remove(block)
        block.editable_label.delete()

    def delete_connection(self, cur_polyline):
        for block in self.list_blocks:
            for rect in block.rectangles[1:]:
                for connection in rect.connect_lines:
                    if connection == cur_polyline:
                        if rect.is_left:
                            dest_el = rect
                        else:
                            source_el = rect

        source_el.parent.connections[source_el.name].remove((dest_el.parent.name, dest_el.name))
        source_el.connect_lines.remove(cur_polyline)
        dest_el.connect_lines.remove(cur_polyline)
        self.polylines_list.remove(cur_polyline)
        self.unsetCursor()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MyMain()
    window.show()
    sys.exit(app.exec_())
