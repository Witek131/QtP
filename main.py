import sys

from PyQt5.QtGui import QPainter, QColor
# Импортируем из PyQt5.QtWidgets классы для создания приложения и виджета
from PyQt5.QtWidgets import QApplication, QMainWindow
from untitled import Ui_MainWindow


# Унаследуем наш класс от простейшего графического примитива QWidget
class Example(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.paint)
        self.do_paint = False

    def paintEvent(self, event):

        self.setWindowTitle('Рисование')
        if self.do_paint:
            paint = QPainter()
            paint.begin(self)
            self.rect(paint)
            paint.end()
            self.do_paint = False

    def paint(self):
        self.do_paint = True
        self.repaint()

    def rect(self, paint):
        paint.setBrush(QColor(255, 0, 0))
        s = int(self.lineEdit_3.text()) + 100
        d = s
        print(s)
        a = 0
        # Рисуем прямоугольник заданной кистью
        for x in range(int(self.lineEdit.text())):
            paint.drawLine(s * x, s * x, d * x*4, s * x)
            paint.drawLine(d * x*4, s * x, d * x* 4, d*4 * x)
            paint.drawLine(d * x*4, s *4 * x,  s * x, d * x)
            paint.drawLine(s * x, d * x, s * x, s * x)
            d = d - int(self.lineEdit_2.text())
            s = s + int(self.lineEdit_2.text())
            a=s
            print(s, d)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())
