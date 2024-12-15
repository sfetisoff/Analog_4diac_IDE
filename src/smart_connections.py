import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPainter, QPen, QCursor, QPolygon
from PyQt5.QtCore import Qt, QLine, QPoint, QRect


class Connection:
    def __init__(self, point_source, point_destination, color='black'):
        self.point_source = point_source
        self.point_destination = point_destination
        self.color = color

        self.source_x = point_source.x()
        self.source_y = point_source.y()
        self.destination_x = point_destination.x()
        self.destination_y = point_destination.y()
        self.draw_triangle()
        if self.source_x < self.destination_x:
            self.simple = True
            self.simple_case()
        else:
            self.simple = False
            self.hard_case()

    def simple_case(self, dx1=None, source=None, destination=None):
        self.dy1 = None
        self.dx2 = None
        if source:
            self.point_source = source
            self.source_x = self.point_source.x()
            self.source_y = self.point_source.y()
        if destination:
            self.point_destination = destination
            self.destination_x = self.point_destination.x()
            self.destination_y = self.point_destination.y()
        if dx1:
            self.dx1 = dx1
        else:
            self.dx1 = abs(self.source_x - self.destination_x) // 2
        self.x1 = self.source_x
        self.x2 = self.x1 + self.dx1
        self.x3 = self.destination_x
        self.y1 = self.source_y
        self.y2 = self.destination_y
        point1 = QPoint(self.x1, self.y1)
        point2 = QPoint(self.x2, self.y1)
        point3 = QPoint(self.x2, self.y2)
        point4 = QPoint(self.x3, self.y2)
        self.rect_line2 = QRect(QPoint(self.x2 - 5, self.y1 - 5), QPoint(self.x2 + 5, self.y2 + 5))
        self.rect_line3 = QRect()
        self.rect_line4 = QRect()
        line1 = QLine(point1, point2)
        line2 = QLine(point2, point3)
        line3 = QLine(point3, point4)
        self.line_array = [line1, line2, line3]
        self.simple = True
        self.draw_triangle()

    def hard_case(self, dx1=20, dx2=20, dy1=None, source=None, destination=None):
        if source:
            self.point_source = source
            self.source_x = self.point_source.x()
            self.source_y = self.point_source.y()
        if destination:
            self.point_destination = destination
            self.destination_x = self.point_destination.x()
            self.destination_y = self.point_destination.y()

        self.dx1 = dx1
        self.dx2 = dx2
        if dy1:
            self.dy1 = dy1
        else:
            self.dy1 = (self.destination_y - self.source_y) // 2
        self.x1 = self.source_x
        self.x2 = self.x1 + self.dx1
        self.x3 = self.destination_x - self.dx2
        self.x4 = self.destination_x
        self.y1 = self.source_y
        self.y2 = self.y1 + self.dy1
        self.y3 = self.destination_y
        point1 = QPoint(self.x1, self.y1)
        point2 = QPoint(self.x2, self.y1)
        point3 = QPoint(self.x2, self.y2)
        point4 = QPoint(self.x3, self.y2)
        point5 = QPoint(self.x3, self.y3)
        point6 = QPoint(self.x4, self.y3)
        self.rect_line2 = QRect(QPoint(self.x2 - 5, self.y1), QPoint(self.x2 + 5, self.y2))
        self.rect_line3 = QRect(QPoint(self.x3, self.y2 - 5), QPoint(self.x2, self.y2 + 5))
        self.rect_line4 = QRect(QPoint(self.x3 - 5, self.y3), QPoint(self.x3 + 5, self.y2))
        line1 = QLine(point1, point2)
        line2 = QLine(point2, point3)
        line3 = QLine(point3, point4)
        line4 = QLine(point4, point5)
        line5 = QLine(point5, point6)
        self.line_array = [line1, line2, line3, line4, line5]
        self.simple = False
        self.draw_triangle()

    def change_coords(self, current_point):
        self.point_destination = QPoint(current_point.x(), current_point.y())
        self.destination_x = current_point.x()
        self.destination_y = current_point.y()
        if self.source_x + 40 < self.destination_x:
            self.simple_case()
        else:
            self.hard_case()
        self.draw_triangle()

    def draw_triangle(self):
        self.triangle_points = [
            self.point_destination,
            QPoint(self.destination_x - 7, self.destination_y - 4),
            QPoint(self.destination_x - 7, self.destination_y + 4)
        ]
        self.triangle = QPolygon(self.triangle_points)
        for i in range(3):
            self.triangle.setPoint(i, self.triangle_points[i])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 600, 600)
        self.setMouseTracking(True)
        self.polylines_list = []
        self.current_connection = None
        self.drawing = False
        self.movable_polyline = None

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(Qt.black, 2)  # Черный цвет, ширина 2
        painter.setPen(pen)
        painter.setBrush(Qt.black)

        for polyline in self.polylines_list:
            for line in polyline.line_array:
                painter.drawLine(line)
            painter.drawPolygon(polyline.triangle)

    def mousePressEvent(self, event):
        self.current_x = event.x()
        self.current_y = event.y()
        self.movable_polyline, self.coord = self.check_moving_connect(event)

        if self.movable_polyline is None:
            self.current_connection = Connection(QPoint(self.current_x, self.current_y),
                                                 QPoint(self.current_x + 1, self.current_y + 2))
            self.polylines_list.append(self.current_connection)
            self.drawing = True  # Установить состояние рисования


    def mouseReleaseEvent(self, event):
        self.current_connection = None
        self.drawing = False  # Сбросить состояние рисования
        x = event.x()
        y = event.y()
        self.movable_polyline = None

        self.update()

    def mouseMoveEvent(self, event):
        self.current_x = event.x()
        self.current_y = event.y()

        if self.drawing:

            self.current_connection.change_coords(event)
        else:
            self.check_moving_connect(event)
            self.change_movable_polyline(event)
        self.update()

    def check_moving_connect(self, event):
        for polyline in self.polylines_list:
            if polyline.rect_line2.contains(event.x(), event.y()):
                self.setCursor(QCursor(Qt.SizeHorCursor))
                return polyline, 'dx1'
            elif polyline.rect_line3.contains(event.x(), event.y()):
                self.setCursor(QCursor(Qt.SizeVerCursor))
                return polyline, 'dy1'
            elif polyline.rect_line4.contains(event.x(), event.y()):
                self.setCursor(QCursor(Qt.SizeHorCursor))
                return polyline, 'dx2'
            else:
                self.unsetCursor()
        return None, None

    def change_movable_polyline(self, event):
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
                                                    dy1=event.y() - self.movable_polyline.y1)
                elif (self.coord == 'dx2') and (self.movable_polyline.x4 - event.x() > 10):
                    self.movable_polyline.hard_case(dx1=self.movable_polyline.dx1,
                                                    dx2=self.movable_polyline.x4 - event.x(),
                                                    dy1=self.movable_polyline.dy1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
