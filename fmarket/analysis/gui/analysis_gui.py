import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ..analysis import Analysis
from .analysis_selection_gui import Analysis_Selection_GUI
import pickle
import pandas as pd

class Analysis_GUI(tk.Tk):
    def __init__(self, symbols=[], update_cache=False):
        super().__init__()
        analysis = Analysis(symbols)
        self.filter_data = analysis.get_filter_data(update_cache=update_cache)
        if self.filter_data.empty:
            print('No symbols available to analyse')
            return
        self.build_gui()
        self.mainloop()

    def build_gui(self):
        self.title('Market Analysis: %s symbols' % self.filter_data.shape[0])
        self.minsize(width=700, height=50) 

        # action buttons frame
        frame_actions = tk.Frame(self)
        frame_actions.pack(anchor='w', fill='x', padx=10, pady=10)

        # filters frame
        self.frame_filters = Frame_Filters(self, self.filter_data)
        self.frame_filters.pack(anchor='w', padx=10, pady=10)

        # add actions
        self.button_add_filter = tk.Button(frame_actions, text='Add Filter', command=self.frame_filters.add_frame_filter)
        self.button_add_filter.pack(side='left')
        tk.Button(frame_actions, text='Save Filters', command=self.save_filters).pack(side='left')
        tk.Button(frame_actions, text='Load Filters', command=self.load_filters).pack(side='left')
        tk.Button(frame_actions, text='Analyze', command=self.analyze).pack(side='right')

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

    def reset_frame_filters(self):
        self.frame_filters.destroy()
        
        self.frame_filters = Frame_Filters(self, self.filter_data)
        self.button_add_filter.config(command=self.frame_filters.add_frame_filter)
        self.frame_filters.pack(anchor='w', padx=10, pady=10)

    def analyze(self):
        symbols, columns = self.get_filtered()
        selection_data = self.filter_data.loc[symbols]
        Analysis_Selection_GUI(self, selection_data)

    def get_filtered(self):
        filters = self.frame_filters.get_filters()
        select = pd.Series(True, index=self.filter_data.index)
        columns = set()
        for filter in filters:
            or_filters = [filter['and']] + filter['or']
            or_select = pd.Series(False, index=self.filter_data.index)
            for or_filter in or_filters:
                column_a = or_filter[0]
                columns.add(column_a)
                function = or_filter[1]
                value = or_filter[2]
                column_b = or_filter[2]
                is_column_b = or_filter[3]

                # set values to be tested
                if column_a == self.filter_data.index.name:
                    test_series = self.filter_data.index
                else:
                    test_series = self.filter_data[column_a]

                # set values to test
                if is_column_b:
                    if column_b == self.filter_data.index.name:
                        value = self.filter_data.index
                    else:
                        value = self.filter_data[column_b]
                elif not isinstance(value, type(None)):
                    try:
                        value = float(value)
                    except:
                        pass

                if function == '==':
                    or_select = or_select | (test_series == value)
                
                elif function == '!=':
                    or_select = or_select | (test_series != value)
                    
                elif function == '>':
                    or_select = or_select | (test_series > value)
                    
                elif function == '<':
                    or_select = or_select | (test_series < value)
                    
                elif function == '>=':
                    or_select = or_select | (test_series >= value)
                    
                elif function == '<=':
                    or_select = or_select | (test_series <= value)

                elif function == 'contains':
                    or_select = or_select | (test_series.str.lower().str.contains(value.lower().replace('^', r'\^')))
                    
                elif function == 'startswith':
                    or_select = or_select | (test_series.str.lower().str.startswith(value.lower()))
                    
                elif function == 'endswith':
                    or_select = or_select | (test_series.str.lower().str.endswith(value.lower()))
                    
                elif function == 'isna':
                    or_select = or_select | (test_series.isna())
                    
                elif function == 'notna':
                    or_select = or_select | (test_series.notna())

            select = select & or_select

        return (sorted(self.filter_data[select].index), columns)

class Frame_Filters(tk.Frame):
    # Frame that collects Frame_Filter widgets
    
    def __init__(self, parent, filter_data):
        super().__init__(parent)
        self.parent = parent
        self.filter_data = filter_data

    def add_frame_filter(self, filter={'and': (), 'or': []}):
        # add a Frame Filter at every button click command
        Frame_Filter(self, self.filter_data, filter=filter).grid(row=self.grid_size()[1], column=0, sticky=tk.W)

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
        self.filter_data = data
        
        # make wide enough se we can see hierachy of or filters
        self.grid_columnconfigure(0, minsize=650)

        # add filter AND to filter
        self.filter = Filter(self, self.filter_data, filter['and'])
        self.filter.grid(row=0, column=0, sticky=tk.W)

        # add OR filters frame to filter
        self.frame_filter_or = Frame_Filter_OR(self, self.filter_data, filter['or'])
        self.frame_filter_or.grid(row=1, column=0, sticky=tk.W, padx=20)

    def remove_filter(self, filter_a):
        self.parent.remove_frame_filter(self)

    def add_filter(self):
        self.frame_filter_or.add_filter()

    def get_filter(self):
        filter = {}
        filter['and'] = self.filter.get_filter()
        filter['or'] = self.frame_filter_or.get_filters()
        return filter

class Frame_Filter_OR(tk.Frame):
    def __init__(self, parent, filter_data, filters=[]):
        super().__init__(parent)
        self.parent = parent
        self.filter_data = filter_data
        if len(filters) > 0:
            for filter in filters:
                self.add_filter(filter)

    def add_filter(self, filter=()):
        Filter(self, self.filter_data, filter=filter).grid(row=self.grid_size()[1], column=0, sticky=tk.W)

    def remove_filter(self, filter_a):
        filter_a.destroy()
        if len(self.winfo_children()) > 0:
            for i, widget in enumerate(self.winfo_children()):
                widget.grid_configure(row=i)
        else:
            self.parent.reset_frame_filter_or()

    def get_filters(self):
        filters = []
        for filter in self.winfo_children():
            filters.append(filter.get_filter())
        return filters

class Filter(tk.Frame):
    def __init__(self, parent, filter_data, filter=()):
        super().__init__(parent)
        self.parent = parent
        self.filter_data = filter_data
        self.filter = filter
        first_params = ['type','sub_type', 'sector', 'industry']
        self.params = [self.filter_data.index.name] + first_params + sorted(set(self.filter_data.columns).difference(first_params))

        # remove filter from parentbutton
        tk.Button(self, text='X', command=lambda: parent.remove_filter(self)).grid(row=0, column=0)

        # add filter to parent button
        tk.Button(self, text='+', command=parent.add_filter).grid(row=0, column=1)

        # add param option entry
        self.replace_entry(2, self.params)

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
        if len(self.filter) > 0:
            self.function_select.set(self.filter[1])
        else:
            self.function_select.set(functions[0])
        function = tk.OptionMenu(self, self.function_select, *functions, command=self.function_changed)
        function.config(width=7)
        function.grid(row=0, column=3)

        self.entry_option = tk.IntVar()
        if len(self.filter) > 3 and self.filter[3]:
                self.entry_option.set(1)
        tk.Checkbutton(self, variable=self.entry_option, command=self.entry_option_changed).grid(row=0, column=4)

        # automatically update second entry by saying the first one changed
        self.entry_changed(None, 2)

    def entry_changed(self, event, column):
        if isinstance(event, tk.Event):
            value = event.widget.get()
        else:
            value = self.grid_slaves(row=0, column=column)[0].get()

        if column == 2:
            # get settings of current filter
            function = self.function_select.get()

            if function in ['isna', 'notna']:
                self.entry_option.set(0)
                self.replace_entry(5, None)
            elif function in ['contains', 'startswith', 'endswith']:
                self.entry_option.set(0)
                self.replace_entry(5, [])
            elif self.entry_option.get() == 0:
                # find possible values for parameter
                if value == self.filter_data.index.name:
                    values = sorted(self.filter_data.index)
                else:
                    values = sorted(self.filter_data[value].dropna().unique())
                
                # too many for selection or not string values, use entry
                if len(values) > 200 or not isinstance(values[0], str):
                    self.replace_entry(5, [])
                else:
                    self.replace_entry(5, values)
            else:
                self.replace_entry(5, self.params)
    
    def replace_entry(self, column, values):
        old_widget = self.grid_slaves(row=0, column=column)
        if len(old_widget) > 0:
            old_widget[0].destroy()
        
        if isinstance(values, type(None)): return

        value = ''
        if len(self.filter) > 0:
            if column == 2:
                value = self.filter[0]
            elif column == 5:
                value = self.filter[2]

        if len(values) > 0:
            entry = ttk.Combobox(self, values=values, width=45, state='readonly')
            entry.current(0)
            if value in values:
                entry.current(values.index(value))
            entry.bind("<<ComboboxSelected>>", lambda event: self.entry_changed(event, column))
            entry.grid(row=0, column=column)
        else:
            entry = tk.Entry(self, width=45)
            entry.insert(tk.END, value)
            entry.grid(row=0, column=column)

    def entry_option_changed(self):
        self.entry_changed(None, 2)
    
    def function_changed(self, function):
        self.entry_changed(None, 2)

    def get_filter(self):
        column = self.grid_slaves(row=0, column=2)[0].get()
        function = self.function_select.get()
        value = self.grid_slaves(row=0, column=5)
        if len(value) == 0:
            value = None
        else:
            value = value[0].get()
        value_is_column = self.entry_option.get() == 1
        return (column, function, value, value_is_column)
    
