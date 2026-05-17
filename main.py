from PyQt5.QtWidgets import QApplication
from editor import GameEditor
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameEditor()
    window.show()
    sys.exit(app.exec_())