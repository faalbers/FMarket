import tkinter as tk
from .scrape import Scrape
from ..utils import Stop
import threading, os
from tkinter.scrolledtext import ScrolledText

class Scrape_GUI(tk.Tk):
    def __init__(self, symbols=[], settings=[]):
        super().__init__()
        self.scrape = Scrape(symbols=symbols, settings=settings)

        self.__build_gui()

        self.mainloop()

    def __build_gui(self):
        self.title('Scrape')
        # self.geometry("1200x800")

        # action buttons frame
        frame_actions = tk.Frame(self)
        frame_actions.pack(anchor='w', fill='x', padx=10, pady=10)

        # add actions
        tk.Button(frame_actions, text='Update Status', command=self.update_status).pack(side='left')
        self.button_update = tk.Button(frame_actions, text='Update', command=self.update)
        self.button_update.pack(side='left')
        tk.Button(frame_actions, text='Update Stop', command=self.update_stop).pack(side='left')
        self.forced_update = tk.BooleanVar()
        tk.Checkbutton(frame_actions, text='forced update',
            variable=self.forced_update).pack(side='left')
        self.params_update = tk.BooleanVar()
        tk.Checkbutton(frame_actions, text='update',
            variable=self.params_update).pack(side='right')
        tk.Button(frame_actions, text='database params', command=self.get_database_params).pack(side='right')

        scrape_info_frame = tk.Frame(self)
        scrape_info_frame.pack()

        check_box_frame = tk.Frame(scrape_info_frame)
        # check_box_frame.pack(anchor='w', padx=10, pady=10)
        check_box_frame.pack(side='left', anchor='nw', padx=10, pady=10)

        # add settings
        self.settings = {}
        for setting, state in self.scrape.settings.items():
            self.settings[setting] = tk.BooleanVar(value=state)
            tk.Checkbutton(check_box_frame, text=setting,
                variable=self.settings[setting], command=self.check_changed).pack(anchor='w')

        self.log_text_widget = ScrolledText(scrape_info_frame, wrap=tk.WORD, width=130, height=50)
        # self.log_text_widget.config(state='disabled')
        # self.log_text_widget.pack(anchor='w', )
        self.log_text_widget.pack(side='left')

    def check_changed(self):
        for setting, variable in self.settings.items():
            self.scrape.settings[setting] = variable.get()
    
    def update_status(self):
        status = self.scrape.update(status_only=True, forced=self.forced_update.get())
        self.scrape_update_status_text(status)
    
    def update_thread(self):
        self.scrape.update(forced=self.forced_update.get())
        self.button_update.config(state=tk.NORMAL)
        self.quit()

    def update(self):
        if os.path.exists('scrape.log'): os.remove('scrape.log')
        self.scrape_update_text()
        self.button_update.config(state=tk.DISABLED)
        thread = threading.Thread(target=self.update_thread)
        thread.start()
    
    def update_stop(self):
        Stop().set

    def get_database_params(self):
        params =self.scrape.get_database_params(update=self.params_update.get())
        params_text = ''
        for db_name, tables in params.items():
            params_text += f'\n{db_name}:\n'
            for table, columns in tables.items():
                params_text += f'\t\t{table}:\n'
                for column in sorted(columns):
                    params_text += f'\t\t\t{column}\n'
        self.scrape_update_status_text(params_text)
        with open('database_params.txt', 'w') as file:
            file.write(params_text)
        
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