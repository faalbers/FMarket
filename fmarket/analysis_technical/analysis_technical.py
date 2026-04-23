from ..globals import *
import yfinance as yf
from ratelimit import limits, sleep_and_retry
import pandas as pd
import numpy as np
import talib as ta
import matplotlib.pyplot as plt
from ..utils import FTime, storage
import logging
from . import states 

class Analysis_Technical():
    def __init__(self, symbols, id):
        self.symbols = sorted(set(symbols))
        self.id = id
        self.last_market_date = FTime().last_market_date
        self.__set_charts()

    @staticmethod
    def __dataframe_plot(df, title='', ylabel='', line=0.0, figsize=(11, 6), dpi=100):
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

    @staticmethod
    def __get_bottoms_recurse(series, peaks, bottoms):
        series_cummin = series.cummin()
        series_cummin_bottom = series[series_cummin == series_cummin.min()]
        
        # recurse through dips
        down_slope_cummin = series_cummin[:series_cummin_bottom.index[0]]
        if down_slope_cummin.shape[0] > 1:
            down_slope_series = series[down_slope_cummin.index]
            def handle_group(group):
                if group.shape[0] < 2: return
                if len(group.unique()) > 1:
                    bottoms.loc[group.index[0]] = group.iloc[0]
                group.name = series.name
                Analysis_Technical.__get_peaks_recurse(group, peaks, bottoms)
            down_slope_series.groupby(down_slope_cummin).apply(handle_group)
        if series_cummin_bottom.shape[0] > 1 and series_cummin_bottom.shape[0] != series.shape[0]:
            bottoms.loc[series_cummin_bottom.index[0]] = series_cummin_bottom.iloc[0]
            Analysis_Technical.__get_peaks_recurse(series_cummin_bottom, peaks, bottoms)
    
    @staticmethod
    def __get_peaks_recurse(series, peaks, bottoms):
        series_cummax = series.cummax()
        series_cummax_peak = series[series_cummax == series_cummax.max()]

        # recurse through dips
        up_slope_cummax = series_cummax[:series_cummax_peak.index[0]]
        if up_slope_cummax.shape[0] > 1:
            up_slope_series = series[up_slope_cummax.index]
            def handle_group(group):
                if group.shape[0] < 2: return
                if len(group.unique()) > 1:
                    peaks.loc[group.index[0]] = group.iloc[0]
                group.name = series.name
                Analysis_Technical.__get_bottoms_recurse(group, peaks, bottoms)
            up_slope_series.groupby(up_slope_cummax).apply(handle_group)
        if series_cummax_peak.shape[0] > 1 and series_cummax_peak.shape[0] != series.shape[0]:
            peaks.loc[series_cummax_peak.index[0]] = series_cummax_peak.iloc[0]
            Analysis_Technical.__get_bottoms_recurse(series_cummax_peak, peaks, bottoms)
    

    @staticmethod
    def __get_trends(series):
        peaks, bottoms = Analysis_Technical.__get_peaks_bottoms(series)

        uptrend_peaks = pd.Series(np.nan, index=series.index, name='uptrend_peaks')
        is_uptrend = peaks.shift(1) < peaks
        is_not_uptrend = peaks.shift(1) > peaks
        uptrend_peaks[is_uptrend] = 1.0
        uptrend_peaks[is_not_uptrend] = 0.0
        uptrend_peaks = uptrend_peaks.bfill()

        uptrend_bottoms = pd.Series(np.nan, index=series.index, name='uptrend_bottoms')
        is_uptrend = bottoms.shift(1) < bottoms
        is_not_uptrend = bottoms.shift(1) > bottoms
        uptrend_bottoms[is_uptrend] = 1.0
        uptrend_bottoms[is_not_uptrend] = 0.0
        uptrend_bottoms = uptrend_bottoms.bfill()

        uptrends = ((uptrend_peaks == 1.0) & (uptrend_bottoms == 1.0)) * 1.0

        downtrend_bottoms = pd.Series(np.nan, index=series.index, name='downtrend_bottoms')
        is_downtrend = bottoms.shift(1) > bottoms
        is_not_uptrend = bottoms.shift(1) < bottoms
        downtrend_bottoms[is_downtrend] = 1.0
        downtrend_bottoms[is_not_uptrend] = 0.0
        downtrend_bottoms = downtrend_bottoms.bfill()
        
        downtrend_peaks = pd.Series(np.nan, index=series.index, name='downtrend_peaks')
        is_downtrend = peaks.shift(1) > peaks
        is_not_uptrend = peaks.shift(1) < peaks
        downtrend_peaks[is_downtrend] = 1.0
        downtrend_peaks[is_not_uptrend] = 0.0
        downtrend_peaks = downtrend_peaks.bfill()

        downtrends = ((downtrend_bottoms == 1.0) & (downtrend_peaks == 1.0)) * 1.0

        trends = pd.Series(0.0, index=series.index, name='trends')
        trends.loc[uptrends == 1.0] = 1.0
        trends.loc[downtrends == 1.0] = -1.0

        return trends, trends.rolling(window=20).mean()

    @staticmethod
    def __get_peaks_bottoms(series):
        peaks = pd.Series(np.nan, index=series.index, name='peaks')
        peaks.iloc[0] = series.iloc[0]
        bottoms = pd.Series(np.nan, index=series.index, name='botoms')
        bottoms.iloc[0] = series.iloc[0]

        search_series = series.copy()
        while search_series.shape[0] > 1:
            series_cummax = search_series.cummax()
            series_cummax_peaks = series_cummax[series_cummax.shift(-1) == series_cummax]
            if series_cummax_peaks.shape[0] == 0:
                series_cummax_peaks = series_cummax.iloc[-1:]
            
            series_cummin = search_series.cummin()
            series_cummin_bottoms = series_cummin[series_cummin.shift(-1) == series_cummin]
            if series_cummin_bottoms.shape[0] == 0:
                series_cummin_bottoms = series_cummin.iloc[-1:]

            if series_cummax_peaks.index[0] != search_series.index[0]:
                peaks.loc[series_cummax_peaks.index[0]] = series.loc[series_cummax_peaks.index[0]]
                search_series = series[series_cummax_peaks.index[0]:]
            elif series_cummin_bottoms.index[0] != search_series.index[0]:
                bottoms.loc[series_cummin_bottoms.index[0]] = series.loc[series_cummin_bottoms.index[0]]
                search_series = series[series_cummin_bottoms.index[0]:]
            else:
                no_slope = search_series[search_series != search_series.iloc[0]]
                search_series = series[no_slope.index[0]:]

        return peaks.ffill(), bottoms.ffill()
    
    def test_test(self):
        date_range = pd.date_range(start='2025-04-20', end='2026-04-20')
        chart = pd.Series(np.nan, index=date_range, name='test')

        values = {
            '2025-04-20': 16,
            '2025-05-20': 30,
            '2025-05-26': 20,
            '2025-06-10': 18,
            '2025-06-25': 36,
            '2025-07-26': 25,
            '2025-08-10': 29,
            '2025-08-25': 45,
            '2025-09-10': 31,
            '2025-09-15': 30,
            '2025-09-25': 35,
            '2025-10-24': 30,
            '2025-10-10': 26,
            '2025-10-15': 27,
            '2025-10-25': 30,
            '2025-11-01': 28,
            '2025-11-10': 26,
            '2025-12-20': 29,
            '2025-12-26': 20,
            '2026-01-10': 18,
            '2026-01-25': 35,
            '2026-02-26': 25,
            '2026-03-10': 29,
            '2026-03-25': 44,
            '2026-03-28': 32,
            '2026-04-10': 34,
            '2026-04-20': 30,
        }
        for date, value in values.items():
            chart[date] = value
        chart = chart.interpolate()

        # peaks, bottoms = Analysis_Technical.__get_peaks_bottoms(chart)
        trends, trend_mean = Analysis_Technical.__get_trends(chart)

        plot_datas = {}
        if True:
            plot_data = chart.to_frame()
            plot_min = chart.min()
            plot_max = chart.max()
            plot_range = plot_max - plot_min
            plot_mid_range = plot_range / 2
            plot_mid = plot_mid_range + plot_min

            plot_data['trends'] = (trend_mean * plot_mid_range) + plot_mid
            plot_data['mid'] = plot_mid
            
            plot_datas['test'] = plot_data

        return plot_datas

    def test(self):
        plot_datas = {}
        for symbol, chart in self.charts.items():
            # if not symbol in ['ASML']: continue
            # if not symbol in ['APH']: continue
            if symbol in ['MVRXX']: continue
            print(symbol)
            chart = chart['Adj Close'].copy()

            trends, trend_mean = Analysis_Technical.__get_trends(chart)

            if True:
                plot_data = chart.to_frame()
                plot_min = chart.min()
                plot_max = chart.max()
                plot_range = plot_max - plot_min
                plot_mid_range = plot_range / 2
                plot_mid = plot_mid_range + plot_min

                # plot_data['trends'] = (trends * plot_mid_range) + plot_mid
                plot_data['trends'] = (trend_mean * plot_mid_range) + plot_mid
                plot_data['mid'] = plot_mid
            

                plot_datas[symbol] = plot_data
        
        return plot_datas


    def is_overbuy(self):
        states_symbols = []
        for symbol, chart in self.charts.items():
            oversell_symbol = states.RSI(chart).apply(lambda x: (x > 70))
            oversell_symbol.name = symbol
            states_symbols.append(oversell_symbol)
        states_symbols = pd.DataFrame(states_symbols).T
        return states_symbols
    
    def is_oversell(self):
        states_symbols = []
        for symbol, chart in self.charts.items():
            oversell_symbol = states.RSI(chart).apply(lambda x: (x < 30))
            oversell_symbol.name = symbol
            states_symbols.append(oversell_symbol)
        states_symbols = pd.DataFrame(states_symbols).T
        return states_symbols
    
    def __get_signals(self, states_list):
        states_data = pd.DataFrame(states_list).any(axis=0)
        print(states_data)
    
    def __get_signals_all(self, states_list):
        states_data = pd.DataFrame(states_list).any(axis=0)
        print(states_data)
    

    def sell(self, bolinger_bands=True):
        uptrends = self.get_uptrends()
        symbols_downtrends = []
        for symbol, uptrend in uptrends.items():
            uptrend = uptrend.dropna()
            if uptrend.dropna().empty: continue
            # if not (uptrend.index[-1] >= self.last_market_date.tz_localize(None)): continue
            if uptrend.iloc[-1]: continue
            symbols_downtrends.append(symbol)

        if not bolinger_bands: return symbols_downtrends
        
        symbols_sell = []
        bolinger_bands = self.bolinger_bands(symbols_downtrends)
        for symbol, bolinger_band in bolinger_bands.items():
            if bolinger_band['Adj Close'].iloc[-1] >= bolinger_band['BB_top'].iloc[-1]:
                symbols_sell.append(symbol)

        return symbols_sell

    def buy(self, bolinger_bands=True):
        uptrends = self.get_uptrends()
        symbols_uptrends = []
        for symbol, uptrend in uptrends.items():
            uptrend = uptrend.dropna()
            if uptrend.dropna().empty: continue
            # if not (uptrend.index[-1] >= self.last_market_date.tz_localize(None)): continue
            if not uptrend.iloc[-1]: continue
            symbols_uptrends.append(symbol)

        if not bolinger_bands: return symbols_uptrends
        
        symbols_buy = []
        bolinger_bands = self.bolinger_bands(symbols_uptrends)
        for symbol, bolinger_band in bolinger_bands.items():
            if bolinger_band['Adj Close'].iloc[-1] <= bolinger_band['BB_bot'].iloc[-1]:
                symbols_buy.append(symbol)

        return symbols_buy
    
    def bolinger_bands(self, symbols=[]):
        bolinger_bands = {}
        if len(symbols) == 0:
            symbols = sorted(self.charts.keys())
        else:
            symbols = sorted(set(self.charts.keys()).intersection(set(symbols)))

        for symbol in symbols:
            chart_work = self.charts[symbol][['Adj Close']].copy()
            chart_work['BB_top'], chart_work['BB_mid'], chart_work['BB_bot'] = ta.BBANDS(chart_work['Adj Close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

            bolinger_bands[symbol] = chart_work[['Adj Close', 'BB_top', 'BB_bot']]
            # chart_work[['Adj Close', 'BB_top', 'BB_bot']].plot(title=symbol)
            # plt.show()

        return bolinger_bands

    @sleep_and_retry
    @limits(calls=100, period=60) # 6000/hour
    def __get_charts_symbol(self, symbol):
        ticker = yf.Ticker(symbol)
        chart = ticker.history(period='1y',auto_adjust=False)
        if chart.empty: return
        chart.index = chart.index.tz_localize(None)
        self.charts[symbol] = chart
    
    def __set_charts(self):
        # make yfinance non verbose
        yflogger = logging.getLogger('yfinance')
        yflogger.disabled = True
        yflogger.propagate = False

        if USE_CACHE_DATA:
        # if False:
            self.charts = storage.load('at_charts_%s' % self.id)
        else:
            self.charts = {}
            for symbol in self.symbols:
                self.__get_charts_symbol(symbol)
            storage.save(self.charts, 'at_charts_%s' % self.id)
