import tkinter as tk
from .scrape import Scrape

class Scrape_GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.scrape = Scrape()

        self.__build_gui()

        self.mainloop()

    def __build_gui(self):
        self.title('Scrape')

        # action buttons frame
        frame_actions = tk.Frame(self)
        frame_actions.pack(anchor='w', fill='x', padx=10, pady=10)

        # add actions
        self.button_add_filter = tk.Button(frame_actions, text='Update All Status', command=self.scrape.update_status)
        self.button_add_filter.pack(side='left')
        self.button_add_filter = tk.Button(frame_actions, text='Update All', command=self.scrape.update)
        self.button_add_filter.pack(side='left')
