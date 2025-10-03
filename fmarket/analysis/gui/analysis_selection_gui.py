import tkinter as tk

class Analysis_Selection_GUI(tk.Toplevel):
    def __init__(self, parent, symbols, columns):
        super().__init__(parent)