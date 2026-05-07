from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from .statusFrame import StatusMessage


class BaseFrame(QDialog):
    def __init__(self, parent=None, title="Base Frame", actionButtonText="Action"):
        super().__init__(parent)
        self.setWindowTitle(title)

        self.main_layout = QVBoxLayout(self)
        self.content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.content_layout)

        self.createMainArea()

        self.status_message = StatusMessage(self)
        self.main_layout.addWidget(self.status_message)

        button_layout = QHBoxLayout()
        self.main_layout.addLayout(button_layout)

        action_button = QPushButton(actionButtonText, self)
        action_button.clicked.connect(self.onAction)
        button_layout.addWidget(action_button)

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

    def createMainArea(self):
        self.content_layout.addWidget(
            QLabel("Override createMainArea() in your frame.", self)
        )

    def onAction(self):
        self.status_message.showMessage(
            "Override onAction() in your frame.",
            success=False,
        )
