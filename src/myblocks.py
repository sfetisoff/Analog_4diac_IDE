from PyQt5.QtCore import QRect, QPoint, Qt
from PyQt5.QtWidgets import QLabel, QLineEdit

from editable_label import EditableLabel

class MyRect(QRect):
    def __init__(self, *args, parent=None, name=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.name = name
        self.connect_lines = []  # Линии связи, связанные с прямоугольником
        self.value = "''"
        self.editable_label = None
        self.value_width = 0
        self.value_height = 0
        self.value_x = None
        self.value_y = None


class MyBlock:
    def __init__(self, main_window, name=None, x=300, y=300, width=100, height=140, color='darkCyan', n_rects_left=4, n_rects_right=4, labels=None):
        self.main_window = main_window
        self.name = name

        self.x = x # Координата х центрального элемента
        self.y = y # Координаты у центрального элемента
        self.width = width
        self.height = height
        self.rectangles = []
        self.labels = labels
        self.type = labels[0]

        self.create_label()

        self.connections = {self.labels[i]: [] for i in range(1,len(self.labels))}
        self.n_rects_left = n_rects_left
        self.n_rects_right = n_rects_right
        self.color = color
        self.cell_height_left = int(self.height / self.n_rects_left)
        self.cell_height_right = int(self.height / self.n_rects_right)
        self.cell_width = int(self.width / 2)
        self.create_rect()
        self.create_rect_values()

    def create_label(self):
        self.label_width = self.width
        self.label_height = 20
        self.label_x = self.x + (self.width - self.label_width) // 2
        self.label_y = self.y - 25
        self.editable_label = EditableLabel(block=self, field='name', text=self.name, main_window=self.main_window,
                                            x=self.label_x, y=self.label_y,
                                            width=self.label_width, height=self.label_height)

    def create_rect_values(self):
        rect_with_values = ['IN', 'IN1', 'IN2', 'IN3', 'IN4', 'QI', 'LABEL']
        for rect in self.rectangles:
            if rect.name in rect_with_values:
                rect.value_width = 50
                rect.value_height = 20
                rect.value_x = rect.x() - rect.value_width
                rect.value_y = rect.y() + (rect.height() - rect.value_height) // 2

                rect.editable_label = EditableLabel(block=self, rect=rect, field='value', text=rect.value,
                                                    main_window=self.main_window,
                                                    x=rect.value_x, y=rect.value_y,
                                                    width=rect.value_width, height=rect.value_height)


    def create_rect(self):
        self.rectangles.append(MyRect(self.x, self.y, self.width, self.height,
                                      name=self.type, parent=self))
        # cell_x_left = self.x
        cell_x_left = self.x - self.cell_width
        for cur_rect in range(self.n_rects_left):
            new_y = int(self.y + (self.height / self.n_rects_left) * cur_rect)
            self.rectangles.append(MyRect(cell_x_left, new_y, self.cell_width, self.cell_height_left,
                                          name=self.labels[1+cur_rect], parent=self))

        # cell_x_right = self.x + int(self.width * 0.75)
        cell_x_right = self.x + self.width
        for cur_rect in range(self.n_rects_right):
            new_y = int(self.y + (self.height / self.n_rects_right) * cur_rect)
            self.rectangles.append(MyRect(cell_x_right, new_y, self.cell_width, self.cell_height_right,
                                          name=self.labels[self.n_rects_left + 1 + cur_rect], parent=self))

    def change_coords(self, current_x, current_y):
        for rect in self.rectangles:
            dx = self.main_window.last_mouse_pos.x() - rect.x()
            dy = self.main_window.last_mouse_pos.y() - rect.y()
            rect.moveTo(current_x - dx, current_y - dy)

            for line in rect.connect_lines:
                if rect.contains(line.p2()): # Проверка, какая из 2 точек линии связи в прямоугольнике
                    line.setP2(QPoint(rect.center().x(), rect.center().y()))
                else:
                    line.setP1(QPoint(rect.center().x(), rect.center().y()))

            self.x = self.rectangles[0].x()
            self.y = self.rectangles[0].y()


class BlockStart(MyBlock):
    def __init__(self, main_window, name='E_RESTART', x=150, y=150):
        super().__init__(main_window, name=name, width=80, height=100, color='white', x=x, y=y,
                         n_rects_left=1, n_rects_right=2, labels=['E_RESTART', 'STOP', 'COLD', 'WARM'])


class BlockA(MyBlock): # INT2INT
    def __init__(self, main_window, name='INT2INT', x=300, y=300):
        super().__init__(main_window, name=name, color='white', x=x, y=y,
                         n_rects_left=2, n_rects_right=2, labels=['INT2INT', 'REQ', 'IN', 'CNF', 'OUT'])


class BlockB(MyBlock): #OUT_ANY_CONSOLE
    def __init__(self, main_window, name='OUT_ANY_CONSOLE',x=300,y=300):
        super().__init__(main_window, name=name, width=140, height=140, color='white', x=x, y=y,
                         n_rects_left=4, n_rects_right=2, labels=['OUT_ANY_CONSOLE','REQ','QI','LABEL','IN','CNF','QO'])


class BlockC(MyBlock):
    def __init__(self, main_window, name='STRING2STRING', x=300, y=300):
        super().__init__(main_window, name=name, color='white', x=x, y=y,
                         n_rects_left=2, n_rects_right=2, labels=['STRING2STRING', 'REQ', 'IN', 'CNF', 'OUT'])


class BlockD(MyBlock):
    def __init__(self, main_window, name='F_ADD', x=300, y=300):
        super().__init__(main_window, name=name, width=75, height=105, color='white', x=x, y=y,
                         n_rects_left=3, n_rects_right=2, labels=['F_ADD', 'REQ', 'IN1', 'IN2', 'CNF', 'OUT'])
