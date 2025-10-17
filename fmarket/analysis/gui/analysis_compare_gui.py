import tkinter as tk
from tkinter import ttk

class Analysis_Compare_GUI(tk.Toplevel):
    def __init__(self, parent, symbols):
        super().__init__(parent)

        self.geometry("1200x800")

        self.frame_top_options = tk.Frame(self)
        self.frame_top_options.pack(fill='x')

        frame_symbols_data = Frame_Symbols_Data(self, symbols)
        frame_symbols_data.pack(expand=True, fill='both')
        self.frame_data = frame_symbols_data.frame_data
        
        self.frame_bottom_options = tk.Frame(self)
        self.frame_bottom_options.pack(side='bottom', fill='x')

class Frame_Symbols_Data(ttk.Frame):
    def __init__(self, parent, symbols):
        super().__init__(parent)
        self.parent = parent

        frame_symbols = Frame_Symbols(self, symbols)
        frame_symbols.pack(side='left', fill='y')
        self.frame_data = Frame_Data(self)
        self.frame_data.pack(side='left', expand=True, fill='both')

    def symbols_changed(self, symbols):
        self.parent.symbols_changed(symbols)
    
class Frame_Symbols(ttk.Frame):
    def __init__(self, parent, symbols):
        super().__init__(parent)
        self.parent = parent

        self.canvas = tk.Canvas(self)
        self.canvas.pack(side='left', fill='both')

        self.frame_checkboxes = tk.Frame(self)
        self.canvas.create_window((0,0), window=self.frame_checkboxes, anchor='nw')

        widest_check = 0
        height_check = 0
        self.symbols_state = {}
        for symbol in symbols:
            self.symbols_state[symbol] = tk.IntVar()
            self.symbols_state[symbol].set(1)
            check_button = tk.Checkbutton(self.frame_checkboxes, text=symbol,
                variable=self.symbols_state[symbol], command=self.check_changed)
            check_button.bind('<MouseWheel>', self.mouse_scroll)
            check_button.bind('<ButtonRelease-1>', self.check_released)
            check_button.pack(anchor='w')
            if check_button.winfo_reqwidth() > widest_check: widest_check = check_button.winfo_reqwidth()
            height_check += check_button.winfo_reqheight()
        self.canvas.config(width=widest_check)
        self.canvas.config(scrollregion=(0,0,widest_check, height_check))

        scrollbar = ttk.Scrollbar(self, orient = 'vertical', command=self.scroll_update)
        self.canvas.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

    def check_changed(self):
        self.parent.symbols_changed(self.get_symbols())
    
    def scroll_update(self, *params):
        if self.canvas.winfo_height() <= self.frame_checkboxes.winfo_height():
            self.canvas.yview(*params)
    
    def mouse_scroll(self, event):
        if self.canvas.winfo_height() <= self.frame_checkboxes.winfo_height():
            self.canvas.yview_scroll(int(-1*(event.delta/120)), 'units')

    def check_released(self, event):
        if event.state & 0x0001:
            # With shift , change state of them
            current_symbol = event.widget.cget('text')
            state_inverse = abs((self.symbols_state[current_symbol].get())-1)
            for symbol, symbol_state in self.symbols_state.items():
                if symbol == current_symbol: continue
                symbol_state.set(state_inverse)

    def get_symbols(self):
        return [symbol for symbol, symbol_state in self.symbols_state.items() if symbol_state.get() == 1]

class Frame_Data(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
