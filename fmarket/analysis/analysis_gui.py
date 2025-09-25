import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .analysis import Analysis
import pickle
import pandas as pd

class Analysis_GUI(tk.Tk):
    def __init__(self, symbols=[], cache=False):
        super().__init__()
        self.data = Analysis(symbols, cache=cache).data
        self.build_gui()
        self.mainloop()

    def build_gui(self):
        self.title('Market Analysis')

        # action buttons frame
        frame_actions = tk.Frame(self)
        frame_actions.pack(anchor='w', fill='x', padx=10, pady=10)

        # filters frame
        self.frame_filters = Frame_Filters(self, self.data)
        self.frame_filters.pack(anchor='w', padx=10, pady=10)

        # add actions
        self.button_add_filter = tk.Button(frame_actions, text='Add Filter', command=self.frame_filters.add_frame_filter)
        self.button_add_filter.pack(side='left')
        tk.Button(frame_actions, text='Save Filters', command=self.save_filters).pack(side='left')
        tk.Button(frame_actions, text='Load Filters', command=self.load_filters).pack(side='left')
        tk.Button(frame_actions, text='Analyze', command=self.analyze).pack(side='right')

        # self.resize_window()

    def save_filters(self):
        filters = self.frame_filters.get_filters()
        if len(filters) == 0:
            messagebox.showinfo('Save Filters', 'No filters to save')
        else:
            file = filedialog.asksaveasfile(filetypes=[('FILTER', '*.filt')], defaultextension='.filt', mode='wb')
            if file != None:
                pickle.dump(filters, file, protocol=pickle.HIGHEST_PROTOCOL)
                file.close()
    
    def load_filters(self):
        file = filedialog.askopenfile(filetypes=[('FILTER', '*.filt')], defaultextension='.filt', mode='rb')
        if file != None:
            filters = pickle.load(file)
            file.close()
            self.reset_frame_filters()
            self.frame_filters.set_filters(filters)

    def analyze(self):
        print('Analyse')

    def reset_frame_filters(self):
        self.frame_filters.destroy()
        
        self.frame_filters = Frame_Filters(self, self.data)
        self.button_add_filter.config(command=self.frame_filters.add_frame_filter)
        self.frame_filters.pack(anchor='w', padx=10, pady=10)

        # self.resize_window()

    def resize_window(self):
        print('resize_window')

class Frame_Filters(tk.Frame):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.parent = parent
        self.data = data

    def add_frame_filter(self, filter={'and': (), 'or': []}):
        print(filter)
        Frame_Filter(self, self.data, filter=filter).grid(row=self.grid_size()[1], column=0, sticky=tk.W)
        # self.parent.resize_window()

    def remove_frame_filter(self, frame_filter_a):
        frame_filter_a.destroy()
        if len(self.winfo_children()) > 0:
            for i, widget in enumerate(self.winfo_children()):
                widget.grid_configure(row=i)
        else:
            self.parent.reset_frame_filters()

    def set_filters(self, filters):
        for filter in filters:
            self.add_frame_filter(filter)

    def get_filters(self):
        filters = []
        for frame_filter in self.winfo_children():
            filters.append(frame_filter.get_filter())
        return filters

class Frame_Filter(tk.Frame):
    def __init__(self, parent, data, filter={'and': (), 'or': []}):
        super().__init__(parent)
        self.parent = parent
        self.data = data
        
        # make wide enough se we can see hierachy of or filters
        self.grid_columnconfigure(0, minsize=650)

        # add filter AND to filter
        self.filter = Filter(self, self.data, filter['and'])
        self.filter.grid(row=0, column=0, sticky=tk.W)

        # add OR filters frame to filter
        self.frame_filter_or = Frame_Filter_OR(self, self.data, filter['or'])
        self.frame_filter_or.grid(row=1, column=0, sticky=tk.W, padx=20)

    def remove_filter(self, filter_a):
        print('Remove Filter')
        self.parent.remove_frame_filter(self)
        # self.parent.resize_window()

    def add_filter(self):
        self.frame_filter_or.add_filter()
        # self.parent.resize_window()

    def get_filter(self):
        filter = {}
        filter['and'] = self.filter.get_filter()
        filter['or'] = self.frame_filter_or.get_filters()
        return filter

class Frame_Filter_OR(tk.Frame):
    def __init__(self, parent, data, filters=[]):
        super().__init__(parent)
        self.parent = parent
        self.data = data
        if len(filters) > 0:
            for filter in filters:
                self.add_filter(filter)

    def add_filter(self, filter=()):
        Filter(self, self.data, filter=filter).grid(row=self.grid_size()[1], column=0, sticky=tk.W)
        # self.parent.resize_window()

    def remove_filter(self, filter_a):
        filter_a.destroy()
        if len(self.winfo_children()) > 0:
            for i, widget in enumerate(self.winfo_children()):
                widget.grid_configure(row=i)
        else:
            self.parent.reset_frame_filter_or()
        # self.parent.resize_window()

    def get_filters(self):
        filters = []
        for filter in self.winfo_children():
            filters.append(filter.get_filter())
        return filters

class Filter(tk.Frame):
    def __init__(self, parent, data, filter=()):
        super().__init__(parent)
        self.parent = parent
        self.data = data

        # remove filter from parentbutton
        tk.Button(self, text='X', command=lambda: parent.remove_filter(self)).grid(row=0, column=0)

        # add filter to parent button
        tk.Button(self, text='+', command=parent.add_filter).grid(row=0, column=1)

        # add param option menu
        first_params = ['type','sub_type', 'sector', 'industry']
        params = [self.data.index.name] + first_params + sorted(set(self.data.columns).difference(first_params))
        self.param_select = tk.StringVar()
        if len(filter) > 0:
            self.param_select.set(filter[0])
        else:
            self.param_select.set(params[0])
        self.param_select.trace('w', self.param_changed)
        self.param = ttk.Combobox(self, textvariable=self.param_select, values=params, width=45, state='readonly')
        self.param_shift = False
        self.param_last = self.param_select.get()
        self.param.grid(row=0, column=2)

        # add function option menu
        functions = [
            '==',
            '!=',
            '>',
            '<',
            '>=',
            '<=',
            'contains',
            'startswith',
            'endswith',
            'isna',
            'notna',
        ]
        self.function_select = tk.StringVar()
        if len(filter) > 0:
            self.function_select.set(filter[1])
        else:
            self.function_select.set(functions[0])
        function = tk.OptionMenu(self, self.function_select, *functions, command=self.function_changed)
        function.config(width=7)
        function.grid(row=0, column=3)

        # add value option menu
        self.value_select = tk.StringVar()
        if len(filter) > 0:
            self.value = tk.Entry(self, width=37)
            self.value.insert(tk.END, filter[2])
            self.value.grid(row=0, column=5)
        else:
            self.value = None
            self.param_changed(self.param_select.get())

    def param_changed(self, *args):
        # create a new one if vreated before
        if not isinstance(self.value, type(None)):
            self.value.destroy()
            self.value = None

        # get settings of current filter
        function = self.function_select.get()
        param = self.param_select.get()

        # these functions do not use values
        if function in ['isna', 'notna']: return

        # these functions do not use multi values selection
        if function in ['contains', 'startswith', 'endswith']:
            self.value = tk.Entry(self, width=37)
            self.value.grid(row=0, column=5)
            return

        # get possible values for param
        self.param_last = param
        if param == self.data.index.name:
            values = sorted(self.data.index)
        else:
            values = sorted(self.data[param].dropna().unique())
        
        # too many for selection or not string values, use entry
        if len(values) > 200 or not isinstance(values[0], str):
            self.value = tk.Entry(self, width=37)
            self.value.grid(row=0, column=5)
            return
        
        # use selection
        self.value_select.set(values[0])
        self.value = ttk.Combobox(self, textvariable=self.value_select, values=values, width=30, state='readonly')
        self.value.grid(row=0, column=5)

    def function_changed(self, function):
        self.param_changed(self.param_select.get())

    def get_filter(self):
        column = self.param_select.get()
        function = self.function_select.get()
        if isinstance(self.value, tk.Entry):
            value = self.value.get()
        else:
            value = self.value_select.get()
        return (column, function, value)
