import sys
from PyQt5 import QtWidgets

from models.database import init_db
from views.main_window import MainWindow


def main():
    init_db()
    app = QtWidgets.QApplication(sys.argv)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
