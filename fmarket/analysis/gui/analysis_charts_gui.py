import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from .analysis_compare_gui import Analysis_Compare_GUI
import pandas as pd
from ..analysis import Analysis
from ...utils import FTime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# TODO: check this oout
# https://lightweight-charts-python.readthedocs.io/en/latest/

class Analysis_Charts_GUI(Analysis_Compare_GUI):
    def __init__(self, parent, symbols):
        super().__init__(parent, symbols)
        self.symbols = symbols
        self.set_charts(symbols)

        self.title('Charts Compare')

        # add top options

        # options for sector relative category
        tk.Label(self.frame_top_options, text='Sector:').pack(side='left')
        sectors = ['N/A'] + self.sectors
        self.sector = tk.StringVar()
        self.sector.set(sectors[0])
        sector = tk.OptionMenu(self.frame_top_options, self.sector, *sectors, command=self.sector_changed)
        sector.pack(side='left')
        
        # options for industry relative category
        tk.Label(self.frame_top_options, text='Industry:').pack(side='left')
        industries = ['N/A']
        self.industry = tk.StringVar()
        self.industry.set(industries[0])
        self.industry_option_menu = tk.OptionMenu(self.frame_top_options, self.industry, *industries, command=self.industry_changed,)
        self.industry_option_menu.pack(side='left')

        # add bottom options

        # date entries
        tk.Label(self.frame_bottom_options, text='Start Date:').pack(side='left')
        self.start_date = DateEntry(self.frame_bottom_options,
            selectmode='day', date_pattern="yyyy-mm-dd")
        self.start_date.bind("<<DateEntrySelected>>", self.date_changed)
        self.start_date.pack(side='left')
        
        tk.Label(self.frame_bottom_options, text='End Date:').pack(side='left')
        self.end_date = DateEntry(self.frame_bottom_options,
            selectmode='day', date_pattern="yyyy-mm-dd")
        self.end_date.bind("<<DateEntrySelected>>", self.date_changed)
        self.end_date.pack(side='left')

        # auto date range
        auto_date_range = [
            'auto date all',
            'auto date ttm',
            'auto date year to date',
            'auto date 3 years',
            'auto date 5 years',
            'no auto date'
        ]
        self.auto_date_range = tk.StringVar()
        self.auto_date_range.set(auto_date_range[0])
        tk.OptionMenu(self.frame_bottom_options, self.auto_date_range, *auto_date_range, command=self.auto_date_range_changed).pack(side='left')

        # sector relative
        self.category_relative = tk.BooleanVar()
        tk.Checkbutton(self.frame_bottom_options, text='category relative',
            variable=self.category_relative,
            command=self.category_relative_changed).pack(side='left')

        # refresh graph
        self.plot_charts()

    
    def symbols_changed(self, symbols):
        self.symbols = symbols
        self.plot_charts()

    def sector_changed(self, sector):
        if sector == 'N/A':
            industry_options = ['N/A']
            self.frame_symbols.set_symbols()
            self.symbols = self.frame_symbols.get_symbols()
            self.category_relative.set(0)
        else:
            industries_sectors = self.industries_sectors.loc[self.industries]
            industries_sectors = sorted(industries_sectors[industries_sectors['sector'] == sector].index)
            industry_options = ['N/A'] + industries_sectors
            self.frame_symbols.clear_symbols()
            self.frame_symbols.set_symbols(self.sector_symbols[sector])
            self.symbols = self.frame_symbols.get_symbols()
            
        
        # update industry options
        self.industry_option_menu['menu'].delete(0, 'end')
        for option in industry_options:
            self.industry_option_menu['menu'].add_command(label=option, command=lambda v=option: self.industry_changed(v))
        self.industry.set(industry_options[0])

        self.plot_charts()

    def industry_changed(self, industry):
        self.industry.set(industry)

        if industry == 'N/A':
            self.sector_changed(self.sector.get())
        else:
            self.frame_symbols.clear_symbols()
            self.frame_symbols.set_symbols(self.industry_symbols[industry])
            self.symbols = self.frame_symbols.get_symbols()
        
        self.plot_charts()

    def category_relative_changed(self):
        if self.sector.get() == 'N/A':
            self.category_relative.set(0)
            return
        self.plot_charts()

    def auto_date_range_changed(self, auto_date_range):
        self.plot_charts()

    def date_changed(self, event):
        self.auto_date_range.set('no auto date')
        self.plot_charts()

    def set_dates(self):
        auto_date_range = self.auto_date_range.get()
        ftime = FTime()
        if auto_date_range == 'no auto date':
            return
        elif auto_date_range == 'auto date all':
            if len(self.symbols) > 0:
                charts = self.charts[self.symbols].ffill().dropna()
                self.start_date.set_date(charts.index[0])
                self.end_date.set_date(charts.index[-1])
        elif auto_date_range == 'auto date ttm':
            end_date = ftime.now_local
            self.start_date.set_date(ftime.get_offset(end_date, years=-1, days=1))
            self.end_date.set_date(end_date)
        elif auto_date_range == 'auto date year to date':
            end_date = ftime.now_local
            self.start_date.set_date(ftime.get_year_begin(end_date))
            self.end_date.set_date(end_date)
        elif auto_date_range == 'auto date 3 years':
            end_date = ftime.now_local
            self.start_date.set_date(ftime.get_offset(end_date, years=-3, days=1))
            self.end_date.set_date(end_date)
        elif auto_date_range == 'auto date 5 years':
            end_date = ftime.now_local
            self.start_date.set_date(ftime.get_offset(end_date, years=-5, days=1))
            self.end_date.set_date(end_date)

    def set_charts(self, symbols):
        analysis = Analysis(symbols)
        symbol_charts = analysis.get_chart()

        # create compare and compare sector
        self.charts = pd.DataFrame()
        for symbol, chart in symbol_charts.items():
            # add compare
            adj_close = chart['adj_close']
            self.charts = self.charts.merge(adj_close, how='outer', left_index=True, right_index=True)
            self.charts = self.charts.rename(columns={'adj_close': symbol})
        
        # self.charts_sectors = analysis.get_chart_sector().ffill().dropna()
        filter_data, self.charts_sectors, self.charts_industries, self.industries_sectors = analysis.get_data()

        # create sectors
        sectors = filter_data['sector'].dropna()
        self.sectors = sorted(sectors.unique())

        self.sector_symbols = {'N/A': symbols}
        for sector_symbol, sector in sectors.items():
            if sector not in self.charts_sectors.columns:
                raise Exception('sector not found: %s' % sector)
            if not sector in self.sector_symbols:
                self.sector_symbols[sector] = []
            self.sector_symbols[sector].append(sector_symbol)

        # create industries
        industries = filter_data['industry'].dropna()
        self.industries = sorted(industries.unique())

        self.industry_symbols = {'N/A': symbols}
        for industry_symbol, industry in industries.items():
            if industry not in self.charts_industries.columns:
                raise Exception('industry not found: %s' % industry)
            if not industry in self.industry_symbols:
                self.industry_symbols[industry] = []
            self.industry_symbols[industry].append(industry_symbol)

    def get_charts(self):
        self.set_dates()
        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()
        return self.charts[self.symbols].ffill().dropna().loc[start_date:end_date].copy()

    def plot_charts(self):
        child_found = False
        for child in self.frame_data.winfo_children():
            child.destroy()
            child_found = True
        if child_found: del(self.canvas)
        
        compare = self.get_charts()
        compare = compare / compare.iloc[0]
        title = 'growth compare'

        if self.category_relative.get():
            sector = self.sector.get()
            industry = self.industry.get()
            if industry != 'N/A':
                title += ': relative to industry: %s' % industry
                compare = compare.merge(
                    self.charts_industries[industry],
                    how='outer', left_index=True, right_index=True)
                compare = compare.ffill().dropna()
                compare[industry] = compare[industry] / compare[industry].iloc[0]
                compare = (compare.T-compare[industry]).T + 1.0
                compare.drop(industry, axis=1, inplace=True)
            elif sector != 'N/A':
                title += ': relative to sector: %s' % sector
                compare = compare.merge(
                    self.charts_sectors[sector],
                    how='outer', left_index=True, right_index=True)
                compare = compare.ffill().dropna()
                compare[sector] = compare[sector] / compare[sector].iloc[0]
                compare = (compare.T-compare[sector]).T + 1.0
                compare.drop(sector, axis=1, inplace=True)
        
        compare = compare - 1.0

        fig, ax = plt.subplots()
        if not compare.empty:
            compare.plot(ax=ax, title=title)
            ax.axhline(y=0.0, color='black', linestyle='--', linewidth=1)
            ax.grid(True, linestyle='--', linewidth=0.5, color='gray')
            for column in compare.columns:
                annotate_x = compare[column].index[-1]
                annotate_y = compare[column].values[-1]
                ax.annotate(column, xy=(annotate_x, annotate_y), fontsize=8, xytext=(2, 2), textcoords='offset points')
        plt.tight_layout()
        self.canvas = FigureCanvasTkAgg(fig, master=self.frame_data)
        self.canvas.get_tk_widget().pack(expand=True, fill='both')
        plt.close(fig)

class Frame_Graph(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        tk.Button(self, text='Test').pack(side='left')
