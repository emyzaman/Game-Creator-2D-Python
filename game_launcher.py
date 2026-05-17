
import json
import os
from PyQt5.QtWidgets import QApplication
from editor import GamePlayerWindow

def launch_game():
    app = QApplication([])
    with open(os.path.join("scenes", "order.json")) as f:
        order = json.load(f)
    if order:
        first_scene = os.path.join("scenes", order[0])
        window = GamePlayerWindow(first_scene)
        window.show()
        app.exec_()

if __name__ == "__main__":
    launch_game()
