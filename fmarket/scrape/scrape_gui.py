import tkinter as tk
from .scrape import Scrape
from ..utils import Stop
import threading, os
from tkinter.scrolledtext import ScrolledText

class Scrape_GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.scrape = Scrape()

        self.__build_gui()

        self.mainloop()

    def __build_gui(self):
        self.title('Scrape')
        # self.geometry("1200x800")

        # action buttons frame
        frame_actions = tk.Frame(self)
        frame_actions.pack(anchor='w', fill='x', padx=10, pady=10)

        # add actions
        button = tk.Button(frame_actions, text='Update All Status', command=self.update_all_status)
        button.pack(side='left')
        self.button_update_all = tk.Button(frame_actions, text='Update All', command=self.update_all)
        self.button_update_all.pack(side='left')
        button = tk.Button(frame_actions, text='Update Stop', command=self.update_stop)
        button.pack(side='left')

        log_frame = tk.Frame(self)
        log_frame.pack()

        self.log_text_widget = ScrolledText(log_frame, wrap=tk.WORD, width=130, height=50)
        # self.log_text_widget.config(state='disabled')
        self.log_text_widget.pack()

    def update_all_status(self):
        status = self.scrape.update(status_only=True)
        self.scrape_update_status_text(status)
    
    def update_all_thread(self):
        self.scrape.update()
        self.button_update_all.config(state=tk.NORMAL)
        self.quit()

    def update_all(self):
        if os.path.exists('scrape.log'): os.remove('scrape.log')
        self.scrape_update_text()
        self.button_update_all.config(state=tk.DISABLED)
        thread = threading.Thread(target=self.update_all_thread)
        thread.start()
    
    def update_stop(self):
        Stop().set

    def scrape_update_status_text(self, status):
        self.log_text_widget.config(state='normal')
        
        # Clear the scrolled text widget
        self.log_text_widget.delete('1.0', tk.END)

        # Insert the content into the scrolled text widget
        self.log_text_widget.insert(tk.END, status)

        self.log_text_widget.configure(state='disabled')

    def scrape_update_text(self):
        log_path = 'scrape.log'
        if os.path.exists(log_path):
            # Read the content of the text file
            with open(log_path, 'r') as file:
                content = file.read()
            
            self.log_text_widget.config(state='normal')

            # Clear the scrolled text widget
            self.log_text_widget.delete('1.0', tk.END)

            # Insert the content into the scrolled text widget
            self.log_text_widget.insert(tk.END, content)

            self.log_text_widget.see(tk.END)

            self.log_text_widget.configure(state='disabled')
        
        # Schedule the next update after 1 second
        self.after(1000, self.scrape_update_text)    