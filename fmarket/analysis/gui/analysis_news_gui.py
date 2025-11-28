from .analysis_compare_gui import Analysis_Compare_GUI
from ..analysis import Analysis
from tkinter import ttk
import tkinter as tk
import webbrowser
import numpy as np

class Analysis_News_GUI(Analysis_Compare_GUI):
    def __init__(self, parent, symbols):
        super().__init__(parent, symbols, single=True)
        self.symbols = self.frame_symbols.get_symbols()
        self.set_news(symbols)
        
        self.title('News')

        self.update_news()

    def set_news(self, symbols):
        analysis = Analysis(symbols)
        self.news = analysis.get_news()

        # sort descending dates and limit to 100
        for symbol in self.news:
            self.news[symbol].sort_index(ascending=False, inplace=True)
            self.news[symbol] = self.news[symbol].head(100)

    def symbols_changed(self, symbols):
        self.symbols = symbols
        self.update_news()

    def update_news(self):
        child_found = False
        for child in self.frame_data.winfo_children():
            child.destroy()
            child_found = True
            print('gone')
        if child_found: del(self.frame_news)

        symbol = self.symbols[0]
        if not symbol in self.news: return
        self.frame_news = Frame_Tree(self.frame_data, self.news[symbol])
        self.frame_news.pack(expand=True, fill='both')

class Frame_Tree(ttk.Frame):
    def __init__(self, parent, news):
        super().__init__(parent)
        self.parent = parent

        style = ttk.Style()
        style.theme_use('default')
        style.configure('Treeview', fieldbackground="#593C3C")

        news = news.reset_index().copy()
        self.url = news['url'].copy()
        news.loc[news['url'].str.startswith('http'), 'url'] = '*'
        news.loc[~(news['url'] == '*'), 'url'] = ''
        news = news[['date', 'url', 'title']]

        tree_scroll = tk.Scrollbar(self)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(self, yscrollcommand=tree_scroll.set, selectmode='extended')
        self.tree.bind('<Control-a>', self.select_all)
        self.tree.bind('<Button-3>', self.right_click)
        self.tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)

        self.tree['columns'] = news.columns.tolist()
        self.tree.column('#0', width=0, stretch=tk.NO)
        self.tree.heading('#0', text='', anchor=tk.W)

        # # Bind Ctrl+A to select all
        # self.tree.bind('<Control-a>', self.select_all)
        # self.tree.bind('<Key>', self.key_pressed)
        # self.tree.bind('<KeyRelease>', self.key_released)
        if len(news.columns) > 0:
            for column in news.columns:
                if column == 'date': self.tree.column(column, anchor=tk.W, width=120, minwidth=120, stretch=tk.NO)
                elif column == 'url': self.tree.column(column, anchor=tk.W, width=20, minwidth=20, stretch=tk.NO)
                else: self.tree.column(column, anchor=tk.W, stretch=tk.YES)
                # self.tree.heading(column, text=column, anchor=tk.W, command = lambda _col=column: self.sort_tree_new(_col, False))
                self.tree.heading(column, text=column, anchor=tk.W)

            for symbol, row in news.iterrows():
                values = []
                for value in row.values:
                    if isinstance(value, float):
                        value = np.round(value, 2)
                    values.append(value)
                self.tree.insert('', 'end', values=values)
        self.tree.focus_set()

    def select_all(self, event=None):
        children = self.tree.get_children()
        self.tree.selection_set(children)

    def right_click(self, event=None):
        for selected_item in self.tree.selection():
            index = self.tree.index(selected_item)
            url = self.url[index]
            if not url.startswith('http'): continue
            webbrowser.open(url)
