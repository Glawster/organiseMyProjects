from PySide6.QtWidgets import QLabel


class StatusMessage(QLabel):
    def __init__(self, parent=None):
        super().__init__("", parent)
        self.clear()

    def showMessage(self, message, success=True):
        color = "green" if success else "red"
        self.setText(message)
        self.setStyleSheet(f"color: {color};")

    def clear(self):
        self.setText("")
        self.setStyleSheet("")
