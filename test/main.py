
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class TestWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.view = TestView(self)
        self.setCentralWidget(self.view)



class TestView(QGraphicsView):
    def __init__(self, parent=None):
        QGraphicsView.__init__(self, parent)
        self.setMouseTracking(True)

    def viewportEvent(self, event):
        print(event)
        return 1


def main():
    app = QApplication([])
    window = TestWindow()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()
