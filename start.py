# start.py
import sys
from PyQt5.QtWidgets import QApplication
from player import VideoPlayer

def main():
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()