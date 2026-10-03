import sys
from PyQt5 import QtWidgets

from views.main_window import MainWindow

def main():
    app = QtWidgets.QApplication(sys.argv)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
