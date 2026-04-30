from PySide6.QtWidgets import QApplication, QLabel

from .baseFrame import BaseFrame


class FrameTemplate(BaseFrame):
    def __init__(self, parent=None):
        super().__init__(parent, title="Frame Template", actionButtonText="Run")

    def createMainArea(self):
        self.content_layout.addWidget(QLabel("Main Area Content", self))

    def onAction(self):
        self.status_message.showMessage("Add your action handler here.")


def main():
    app = QApplication.instance() or QApplication([])
    frame = FrameTemplate()
    frame.show()
    app.exec()


if __name__ == "__main__":
    main()
