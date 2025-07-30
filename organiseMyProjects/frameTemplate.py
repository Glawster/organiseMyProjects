import tkinter as tk
from tkinter import ttk

from ui.baseFrame import BaseFrame
from logic.logUtils import logger

from globalVars import PAD_X, PAD_Y, PAD_Y_TOP, PAD_X_LEFT

class FrameTemplate(BaseFrame):

    def __init__(self, parent):
        super().__init__(parent, title="your title here")

    def createMainArea(self):
        super().createMainArea()
        lblMain = ttk.Label(self.frmMain, text="Main Area Content")
        lblMain.pack(padx=PAD_X, pady=PAD_Y)

    def onAction(self):
        logger.info("action button clicked...")

    def browseFolder(self):
        logger.info("browse folder clicked...")
