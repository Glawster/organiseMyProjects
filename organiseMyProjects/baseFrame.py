import tkinter as tk
from tkinter import ttk, filedialog

from ui.styleUtils import configureButtonStyle
from ui.statusFrame import StatusMessage
from globalVars import getAppTitle, PAD_X, PAD_Y, PAD_Y_TOP, PAD_X_LEFT

from src.logUtils import logger
from src.editSettings import Settings

class BaseFrame(tk.Toplevel):

    def __init__(self, parent, title="base frame", actionButtonText="Action"):

        logger.info(f"creating frame template: {self.__class__.__name__.lower()}...")
        super().__init__(parent)
        self.master = parent

        # dry run flag defaults to inverse of global execute setting
        self.varDryRun = tk.BooleanVar(value=not Settings.getExecute())

        configureButtonStyle()
        self.title(getAppTitle(title))
        self.actionButtonText = actionButtonText

        self.transient(parent)
        self.grab_set()
        self.focus_set()
        self.lift()
        self.attributes("-topmost", 1)
        self.after(10, lambda: self.attributes("-topmost", 0))

        self.frmContainer = ttk.Frame(self)
        self.frmContainer.pack(fill="both", expand=True)
        self.frmContainer.columnconfigure(0, weight=1)

        self.createFrame()

    def createFrame(self):
        self.createMainArea()
        self.createFolderFrame()
        self.createButtonFrame()

    def createMainArea(self):
        self.frmMain = ttk.Frame(self)
        self.frmMain.pack(pady=PAD_Y, padx=PAD_X)

    def createFolderFrame(self):

        ttk.Label(self, text="Select a folder to...:").pack(anchor="w", padx=PAD_X, pady=PAD_Y_TOP)

        frmFolder = ttk.Frame(self)
        frmFolder.pack(pady=PAD_X, padx=PAD_Y, anchor="w")

        ttk.Label(frmFolder, text="Folder:").pack(side=tk.LEFT, padx=PAD_X_LEFT)
        self.entryFolder = ttk.Entry(frmFolder, width=50)
        self.entryFolder.pack(side=tk.LEFT, padx=PAD_X_LEFT)

        if not self.entryFolder.get():
            self.entryFolder.insert(0, Settings.getPhotoRoot())

        ttk.Button(frmFolder, text="Browse", style="compactButton.TButton", command=self.onBrowseFolder).pack(side=tk.LEFT)

    def createButtonFrame(self):

        frmButtons = ttk.Frame(self)
        frmButtons.pack(pady=PAD_Y)

        self.statusField = StatusMessage(frmButtons)
        self.statusField.frame.pack(fill=tk.X, padx=PAD_X, pady=PAD_Y_TOP)

        ttk.Checkbutton(frmButtons, text="Dry Run", variable=self.varDryRun).pack(side=tk.LEFT, padx=PAD_X)

        ttk.Button(frmButtons, text=self.actionButtonText, style="primaryButton.TButton", command=self.onAction).pack(side=tk.LEFT, padx=PAD_X)
        ttk.Button(frmButtons, text="Close", style="primaryButton.TButton", command=self.destroy).pack(side=tk.LEFT, padx=PAD_X)

    def getFolder(self):
        return self.entryFolder.get()

    def onBrowseFolder(self):

        logger.info("...launching folder picker")
        selected = filedialog.askdirectory(initialdir=self.entryFolder.get())
        if selected:
            self.entryFolder.delete(0, tk.END)
            self.entryFolder.insert(0, selected)

    def onAction(self):
        logger.info("onAction not implemented...")
