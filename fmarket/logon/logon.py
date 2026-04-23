from ..portfolio import Portfolio
from ..analysis_technical import Analysis_Technical
from ..utils import Settings
import pandas as pd
import matplotlib.pyplot as plt


class Logon:
    
    def __init__(self):
        plt.style.use('tableau-colorblind10')
        # update Portfolio and get position symbols
        # self.analysis_sell = Analysis_Technical(Portfolio(update=True).get_symbols(), 'sell')
        self.analysis_sell = Analysis_Technical(Portfolio().get_symbols(), 'sell')
        self.analysis_buy = Analysis_Technical(sorted(Settings().get_ssel('portfolio/buy').index), 'buy')
        symbols_all = sorted(set(Portfolio().get_symbols()+sorted(Settings().get_ssel('portfolio/buy').index)))
        self.analysis_all = Analysis_Technical(symbols_all, 'all')
    
    def test(self):
        # result = self.analysis_sell.is_overbuy()
        # trend = self.analysis_sell.trend()
        charts = self.analysis_all.test()
        for symbol, chart in charts.items():
            Logon.__dataframe_plot(chart, symbol)
            plt.show()
    
    def graph_sell(self):
        Logon.__adj_close_graph(self.analysis_sell.charts, 'Sell')

    def graph_buy(self):
        Logon.__adj_close_graph(self.analysis_buy.charts, 'Buy')

    @staticmethod
    def __adj_close_graph(charts, title):
        prices = pd.DataFrame()
        for symbol, chart in charts.items():
            symbol_chart = chart['Adj Close']
            symbol_chart.name = symbol
            prices = pd.concat([prices, symbol_chart], axis=1)
        prices = (prices / prices.iloc[0]) - 1
        Logon.__dataframe_plot(prices, title, ylabel='growth mult')
        plt.show()

    @staticmethod
    def __dataframe_plot(df, title, ylabel='', line=0.0, figsize=(11, 6), dpi=100):
        df = df.dropna(axis=1, how='all')
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        df.plot(ax=ax, title=title, legend=False)
        for line2d in ax.get_lines():
            label = line2d.get_label()
            color = line2d.get_color()
            last_value = df[label].dropna()
            annotate_x = last_value.index[-1]
            annotate_y = last_value.values[-1]
            ax.annotate(label, xy=(annotate_x, annotate_y),
                fontsize=8, fontweight='bold', xytext=(2, 2), textcoords='offset points', color=color)
        ax.grid(True, linestyle='--', linewidth=0.5, color='gray')
        # ax.axhline(y=line, color='black', alpha=0.5, linestyle='--', linewidth=1)
        ax.set_ylabel(ylabel, fontweight='bold')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: '{:.0f}'.format(x)))
        plt.tight_layout()
        return fig

