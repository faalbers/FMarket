import tkinter as tk
from .analysis_compare_gui import Analysis_Compare_GUI
from ..analysis import Analysis
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Analysis_Fundamentals_GUI(Analysis_Compare_GUI):
    def __init__(self, parent, symbols):
        super().__init__(parent, symbols)
        self.symbols = symbols
        self.set_fundamentals(symbols)

        self.title('Fundamentals Compare')

        data_type = [
            'current ratio',
            'cash ratio',
            'gross profit margin',
            'operating profit margin',
            'profit margin',
            'net profit margin',
            'free cash flow',
            'total revenue',
        ]
        self.data_type = tk.StringVar()
        self.data_type.set(data_type[0])
        tk.OptionMenu(self.frame_bottom_options, self.data_type, *data_type, command=self.data_type_changed).pack(side='left')

        data_period = [
            'yearly',
            'quarterly',
        ]
        self.data_period = tk.StringVar()
        self.data_period.set(data_period[0])
        tk.OptionMenu(self.frame_bottom_options, self.data_period, *data_period, command=self.data_period_changed).pack(side='left')

        # refresh graph
        self.plot_fundamentals()

    def data_type_changed(self, data_type):
        self.plot_fundamentals()

    def data_period_changed(self, data_type):
        self.plot_fundamentals()

    def symbols_changed(self, symbols):
        self.symbols = symbols
        self.plot_fundamentals()

    def set_fundamentals(self, symbols):
        analysis = Analysis(symbols)
        self.fundamentals = analysis.get_fundamentals()
        fundamentals_ttm = self.fundamentals['ttm'].T
        for parameter, data in self.fundamentals['yearly'].items():
            if parameter in fundamentals_ttm.index:
                param_ttm = fundamentals_ttm.loc[parameter].dropna()
                if not param_ttm.empty:
                    if not data.empty:
                        data.loc['ttm'] = param_ttm
                    else:
                        data.loc['ttm'] = pd.DataFrame(param_ttm).T

    def get_fudamentals(self):
        data_type = self.data_type.get()
        y_label = data_type + ' %'
        if data_type in ['free cash flow', 'total revenue']:
            y_label = data_type + ' (millions)'

        data_period = self.data_period.get()
        x_label = data_period.rstrip('ly')
        
        data = self.fundamentals[data_period][data_type].copy()
        if not data.empty and data_period == 'quarterly':
            data.index = data.index.date
        symbols = [s for s in data.columns if s in self.symbols]
        data = data[symbols]
        data.dropna(axis=0, how='all', inplace=True)

        return data, x_label, y_label

    def plot_fundamentals(self):
        child_found = False
        for child in self.frame_data.winfo_children():
            child.destroy()
            child_found = True
        if child_found: del(self.canvas)

        fundamentals, x_label, y_label = self.get_fudamentals()

        fig, ax = plt.subplots()
        if not fundamentals.empty:
            fundamentals.plot(ax=ax, kind='bar')
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.grid(True, linestyle='--', linewidth=0.5, color='gray')
        plt.tight_layout()
        self.canvas = FigureCanvasTkAgg(fig, master=self.frame_data)
        self.canvas.get_tk_widget().pack(expand=True, fill='both')
        plt.close(fig)

