from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget

from .styleUtils import applyApplicationStyle


class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Menu")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Main Menu", self))

        exit_button = QPushButton("Exit", self)
        exit_button.clicked.connect(self.close)
        layout.addWidget(exit_button)


def mainMenu():
    app = QApplication.instance() or QApplication([])
    applyApplicationStyle(app)
    window = MainMenu()
    window.show()
    app.exec()


if __name__ == "__main__":
    mainMenu()
