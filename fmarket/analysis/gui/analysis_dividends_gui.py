import tkinter as tk
from .analysis_compare_gui import Analysis_Compare_GUI
from ..analysis import Analysis
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Analysis_Dividends_GUI(Analysis_Compare_GUI):
    def __init__(self, parent, symbols):
        super().__init__(parent, symbols)
        self.symbols = symbols
        self.set_dividends(symbols)

        self.title('Dividends Compare')

        # add bottom options

        # add date range
        date_range = [
            'yearly',
            'ttm',
            'last year',
            'last ttm',
            'all',
        ]
        self.date_range = tk.StringVar()
        self.date_range.set(date_range[0])
        tk.OptionMenu(self.frame_bottom_options, self.date_range, *date_range, command=self.date_range_changed).pack(side='left')

        # refresh graph
        self.plot_dividends()

    def date_range_changed(self, date_range):
        self.plot_dividends()

    def set_dividends(self, symbols):
        analysis = Analysis(symbols)
        self.dividends = analysis.get_dividend_yields()

    def symbols_changed(self, symbols):
        self.symbols = symbols
        self.plot_dividends()

    def get_dividends(self):
        date_range = self.date_range.get()
        print(date_range)
        y_label = 'Yield %'
        now = pd.Timestamp.now()
        last_year = now.year - 1
        if date_range == 'yearly':
            x_label = 'Year'
            dividends = self.dividends['yearly']
            dividends = dividends[[c for c in self.symbols if c in dividends.columns]].copy()
            dividends.dropna(axis=0, how='all', inplace=True)
        elif date_range == 'ttm':
            x_label = 'Year ttm'
            dividends = self.dividends['ttm']
            dividends = dividends[[c for c in self.symbols if c in dividends.columns]].copy()
            dividends.dropna(axis=0, how='all', inplace=True)
        elif date_range == 'last year':
            x_label = 'Date'
            dividends = self.dividends['all']
            dividends = dividends[[c for c in self.symbols if c in dividends.columns]].copy()
            dividends.dropna(axis=0, how='all', inplace=True)
            dividends = dividends[dividends.index.year == last_year]
            dividends.index = dividends.index.date
        elif date_range == 'last ttm':
            x_label = 'Date'
            dividends = self.dividends['all']
            dividends = dividends[[c for c in self.symbols if c in dividends.columns]].copy()
            dividends.dropna(axis=0, how='all', inplace=True)
            start_date = now.normalize() - pd.DateOffset(years=1) + pd.DateOffset(days=1)
            dividends = dividends.loc[start_date:]
            dividends.index = dividends.index.date
        elif date_range == 'all':
            x_label = 'Date'
            dividends = self.dividends['all']
            dividends = dividends[[c for c in self.symbols if c in dividends.columns]].copy()
            dividends.dropna(axis=0, how='all', inplace=True)
            dividends.index = dividends.index.date
        
        return dividends, x_label, y_label

    def plot_dividends(self):
        child_found = False
        for child in self.frame_data.winfo_children():
            child.destroy()
            child_found = True
        if child_found: del(self.canvas)

        dividends, x_label, y_label = self.get_dividends()

        fig, ax = plt.subplots()
        if not dividends.empty:
            dividends.plot(ax=ax, kind='bar')
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.grid(True, linestyle='--', linewidth=0.5, color='gray')
            # ax.legend(['%s ($%s)' % (c, round(self.analysis_data.loc[c, 'price'], 2)) for c in dividends.columns])
        plt.tight_layout()
        self.canvas = FigureCanvasTkAgg(fig, master=self.frame_data)
        self.canvas.get_tk_widget().pack(expand=True, fill='both')
        plt.close(fig)
