def applyApplicationStyle(app):
    app.setStyleSheet(
        """
        QWidget {
            font-family: "Segoe UI";
            font-size: 10pt;
        }
        QPushButton {
            padding: 6px 12px;
        }
        """
    )
