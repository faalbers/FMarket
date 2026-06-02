from ..globals import *
import yfinance as yf
from ratelimit import limits, sleep_and_retry
import pandas as pd
import numpy as np
import talib as ta
import matplotlib.pyplot as plt
import matplotlib.ticker as plt_ticker
import seaborn as sns
from scipy.signal import savgol_filter, argrelextrema, find_peaks
from ..utils import FTime, storage
import logging
from . import states 
from . import trace

from sklearn.neighbors import KernelDensity

class Analysis_Technical():
    def __init__(self, symbols, id):
        self.symbols = sorted(set(symbols))
        if len(self.symbols) == 0:
            raise ValueError("No valid symbols provided")
        if len(self.symbols) > 100:
            raise ValueError("Too many symbols provided (max limit is 100)")
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

    def trend(self):
        chart_symbols = self.charts.columns.levels[0]
        for symbol in chart_symbols:
            # if not symbol in ['MVRXX']: continue
            # chart = self.charts.loc[:'2026-02-03', symbol].copy()
            print(symbol)
            chart = self.charts.loc[:, symbol].copy().ffill()
            if chart.dropna().empty: continue
            Analysis_Technical.__get_trend(chart, symbol = symbol)
            # Analysis_Technical.__get_slopes(chart, symbol = symbol)


            
    @staticmethod
    def __get_extrema(chart, order=3, sigma=0.03):
        close = chart['Close']
        high = chart['High']
        low = chart['Low']
        
        maxima_np = argrelextrema(close[:-1-order].values, np.greater, order=order)
        minima_np = argrelextrema(close[:-1-order].values, np.less, order=order)
        extrema_np = np.sort(np.concatenate([maxima_np, minima_np], axis=1))[0]
        
        extrema = chart[['Close', 'High', 'Low']].copy()
        extrema['maxima'] = np.nan
        extrema['maxima'].iloc[maxima_np] = high.iloc[maxima_np]
        extrema['minima'] = np.nan
        extrema['minima'].iloc[minima_np] = low.iloc[minima_np]
        extrema['extrema'] = extrema['maxima'].combine_first(extrema['minima'])
        
        # extrema['extrema'] = np.nan
        # extrema['extrema'].iloc[extrema_np] = close.iloc[extrema_np]

        tops, bottoms = trace.directional_change(
            close.to_numpy(),
            high.to_numpy(),
            low.to_numpy(),
            sigma=sigma)

        tops_index = [t[1] for t in tops]
        extrema['maxima_change'] = extrema.iloc[tops_index]['High']
        bottoms_index = [b[1] for b in bottoms]
        extrema['minima_change'] = extrema.iloc[bottoms_index]['Low']
        extrema['extrema_change'] = extrema['maxima_change'].combine_first(extrema['minima_change'])

        # peeks on filtered highs and lows
        atr_window = 14
        atr_rolling_window = 30
        atr = ta.ATR(extrema['High'].values, extrema['Low'].values, extrema['Close'].values, timeperiod=atr_window)
        atr = ta.SMA(atr, timeperiod=atr_rolling_window)
        prominence = atr/2.0
        
        window_length = 49
        polyorder = 5
        high_filtered = savgol_filter(chart['High'], window_length=window_length, polyorder=polyorder)
        peaks, _ = find_peaks(high_filtered,
            # height=750,
            distance = 15, # Minimum horizontal sample distance between peaks
            prominence=prominence, # minimum distance between top value and highest dip on both sides
            # width = 3, # Minimum peak width in samples
        )
        extrema['maxima_filtered'] = np.nan
        extrema['maxima_filtered'].iloc[peaks] = high_filtered[peaks]

        low_filtered = savgol_filter(chart['Low'], window_length=window_length, polyorder=polyorder)
        dips, _ = find_peaks(-low_filtered,
            # height=750,
            distance = 15, # Minimum horizontal sample distance between peaks
            prominence=prominence, # minimum distance between top value and highest dip on both sides
            # width = 3, # Minimum peak width in samples
        )
        extrema['minima_filtered'] = np.nan
        extrema['minima_filtered'].iloc[dips] = low_filtered[dips]
        extrema['extrema_filtered'] = extrema['maxima_filtered'].combine_first(extrema['minima_filtered'])
        extrema['high_filtered'] = high_filtered
        extrema['low_filtered'] = low_filtered
        
        return extrema




    @staticmethod
    def __get_trend_tutorial(chart, order=3, symbol='NONE'):
        # https://youtu.be/v3z3FuxLzjU

        print(symbol)
        # print(chart.tail(20))

        atr_window = 14
        rolling_window = 30
        peaks_start = atr_window + rolling_window -1

        chart = chart.reset_index()

        chart['atr'] = ta.ATR(chart['High'].values, chart['Low'].values, chart['Close'].values, timeperiod=atr_window)
        chart['atr'] = chart['atr'].rolling(window=rolling_window).mean()
        chart['Close_smooth'] = savgol_filter(chart['Close'], window_length=49, polyorder=5)
        prominence = chart['atr'].values/2.0
        peaks, _ = find_peaks(chart['Close_smooth'],
            # height=750,
            distance = 15, # Minimum horizontal sample distance between peaks
            prominence=prominence, # minimum distance between top value and highest dip on both sides
            # width = 3, # Minimum peak width in samples
        )
        chart['peaks'] = chart.iloc[peaks]['Close_smooth']
        dips, _ = find_peaks(-chart['Close_smooth'],
            # height=750,
            distance = 15, # Minimum horizontal sample distance between peaks
            prominence=prominence, # minimum distance between top value and highest dip on both sides
            # width = 3, # Minimum peak width in samples
        )
        chart['dips'] = chart.iloc[dips]['Close_smooth']
        
        # chart.set_index('index', inplace=True)

        fig, ax = plt.subplots(figsize=(10, 6))
        plt.xticks(rotation=30)
        ax.grid(True, linestyle='--', linewidth=1.0, color='black', alpha=0.1)
        ax.plot(chart.index, chart['Close_smooth'], color='blue', zorder=5)
        sns.scatterplot(data = chart['Close_smooth'], ax=ax, color='blue', zorder=5, s=20, alpha=0.3)
        # plt.vlines(x, ymin=y_low, ymax=y_high, colors='teal', linestyles='solid', label='Range')
        
        if False:
            plt.vlines(chart.index, ymin=chart['Close_smooth']-prominence, ymax=chart['Close_smooth'], color='blue', zorder=5, alpha=0.3)
            sns.scatterplot(data = chart['peaks'], ax=ax, color='red', s=100)
            sns.scatterplot(data = chart['dips'], ax=ax, color='green', s=100)
        else:
            extremas = chart['peaks'].combine_first(chart['dips']).interpolate(method='linear', limit_area='inside')
            print(extremas.dropna())
            ax.plot(chart.index, extremas, color='orange', alpha=1.0, zorder=5)
        
        plt.show()

    @staticmethod
    def __get_slopes(series, order=3, symbol='NONE'):
        extrema = Analysis_Technical.__get_extrema(series, order=order)
        extrema.reset_index(inplace=True)

        fig, axs = plt.subplots(figsize=(10, 8))
        axs.plot(extrema[['high_filtered', 'low_filtered']], zorder=5)
        sns.scatterplot(data=extrema['maxima_filtered'],ax=axs, color='red', s=20)
        sns.scatterplot(data=extrema['minima_filtered'],ax=axs, color='green', s=20)
        plt.show()
    
    @staticmethod
    def __get_trend(series, order=3, symbol='NONE'):
        extrema = Analysis_Technical.__get_extrema(series, order=order)
        extrema_ffill = extrema.ffill()

        maxima_name = 'maxima_filtered'
        minima_name = 'minima_filtered'

        # up trend
        HH = pd.Series(None, dtype='boolean', index=extrema.index, name='HH')
        HH.loc[extrema_ffill[maxima_name] > extrema_ffill[maxima_name].shift(1)] = True
        HH.loc[extrema_ffill[maxima_name] < extrema_ffill[maxima_name].shift(1)] = False
        HH = HH.ffill()

        HL = pd.Series(None, dtype='boolean', index=extrema.index, name='HL')
        HL.loc[extrema_ffill[minima_name] > extrema_ffill[minima_name].shift(1)] = True
        HL.loc[extrema_ffill[minima_name] < extrema_ffill[minima_name].shift(1)] = False
        HL = HL.ffill()

        HH_trend = (HH & HL) * 1.0

        # down trend
        LH = pd.Series(None, dtype='boolean', index=extrema.index, name='LH')
        LH.loc[extrema_ffill[maxima_name] < extrema_ffill[maxima_name].shift(1)] = True
        LH.loc[extrema_ffill[maxima_name] > extrema_ffill[maxima_name].shift(1)] = False
        LH = LH.ffill()
        
        LL = pd.Series(None, dtype='boolean', index=extrema.index, name='LL')
        LL.loc[extrema_ffill[minima_name] < extrema_ffill[minima_name].shift(1)] = True
        LL.loc[extrema_ffill[minima_name] > extrema_ffill[minima_name].shift(1)] = False
        LL = LL.ffill()

        LL_trend = (LH & LL) * -1.0

        # trend
        trend = HH_trend + LL_trend
        trend_rolling = trend.rolling(window=20).mean()

        plot_data_0 = trend.to_frame()
        plot_data_1 = trend_rolling.to_frame()
        plot_data_2 = extrema[[maxima_name, minima_name]].copy()
        plot_data_2_b = extrema[['high_filtered', 'low_filtered']].copy()
        
        reset_index = True
        if reset_index:
            plot_data_0.reset_index(inplace=True, drop=True)
            plot_data_1.reset_index(inplace=True, drop=True)
            plot_data_2.reset_index(inplace=True, drop=True)
            plot_data_2_b.reset_index(inplace=True, drop=True)
        

        fig, axs = plt.subplots(3, 1, gridspec_kw={'height_ratios': [0.5, 0.5, 2.5]}, sharex=True, figsize=(10, 8))

        plot_data_0.plot (ax=axs[0], title='trend')
        plot_data_1.plot (ax=axs[1], title='trend_rolling')
        plot_data_2_b.plot (ax=axs[2], title=symbol)
        sns.scatterplot(data=plot_data_2,ax=axs[2], color='red', s=100)
        

        # sns.scatterplot(data=plot_data['HH'],ax=axs[0], color='blue', s=20)
        # sns.scatterplot(data=plot_data['HL'],ax=axs[1], color='blue', s=20)

        for ax in axs:
            if reset_index:
                ax.xaxis.set_major_locator(plt_ticker.MultipleLocator(7*5*4))
                ax.xaxis.set_minor_locator(plt_ticker.MultipleLocator(7*5))
                ax.grid(True, linestyle='--', linewidth=1.0, color='gray', which='major', alpha=0.7)
                ax.grid(True, linestyle='--', linewidth=0.5, color='gray', which='minor', alpha=0.5)
            else:
                ax.grid(True, linestyle='--', linewidth=1.0, color='gray', alpha=0.7)

        plt.tight_layout()
        plt.show()

        # extrema['trend'].replace(np.nan, 0.5).loc[start_date:].plot(ax=ax1, title='trend')


        # # (HH * 1.0).loc[start_date:].plot(ax=ax1, title='trend')
        # # ax1.axhline(0, color='green', linestyle='--')
        
        # extrema[['Close', maxima_name, minima_name]].loc[start_date:].plot (ax=ax2, title=symbol)
        
        # ax1.grid(True, linestyle='--', linewidth=1.0, color='gray', which='major')
        # ax1.grid(True, linestyle='--', linewidth=0.5, color='gray', which='minor')
        
        # ax2.xaxis.set_major_locator(plt_ticker.MultipleLocator(28))
        # ax2.xaxis.set_minor_locator(plt_ticker.MultipleLocator(7))
        # ax2.grid(True, linestyle='--', linewidth=1.0, color='gray', which='major')
        # ax2.grid(True, linestyle='--', linewidth=0.5, color='gray', which='minor')
        

    @staticmethod
    def __get_trend_old(series, order=3, symbol='NONE'):
        extrema = Analysis_Technical.__get_extrema(series, order=order).ffill()

        maxima_name = 'maxima_filtered'
        # maxima_name = 'maxima_change'
        minima_name = 'minima_filtered'
        # minima_name = 'minima_change'
        
        # up trend
        HH = pd.Series(None, dtype='boolean', index=extrema.index, name='HH')
        HH.loc[extrema[maxima_name] > extrema[maxima_name].shift(1)] = True
        HH.loc[extrema[maxima_name] < extrema[maxima_name].shift(1)] = False
        HH = HH.bfill()
        
        HL = pd.Series(None, dtype='boolean', index=extrema.index, name='HL')
        HL.loc[extrema[minima_name] > extrema[minima_name].shift(1)] = True
        HL.loc[extrema[minima_name] < extrema[minima_name].shift(1)] = False
        HL = HL.ffill()

        extrema['HH_trend'] = (HH & HL) * 1.0

        # down trend
        LH = pd.Series(None, dtype='boolean', index=extrema.index, name='LH')
        LH.loc[extrema[maxima_name] < extrema[maxima_name].shift(1)] = True
        LH.loc[extrema[maxima_name] > extrema[maxima_name].shift(1)] = False
        LH = LH.bfill().ffill()
        
        LL = pd.Series(None, dtype='boolean', index=extrema.index, name='LL')
        LL.loc[extrema[minima_name] < extrema[minima_name].shift(1)] = True
        LL.loc[extrema[minima_name] > extrema[minima_name].shift(1)] = False
        LL = LL.ffill().bfill()

        extrema['LL_trend'] = (LH & LL) * -1.0

        # trend
        extrema['trend'] = extrema['HH_trend'] + extrema['LL_trend']
        extrema['trend_rolling'] = extrema['trend'].rolling(window=20).mean()

        start_date = '2026-02-01'
        fig, (ax1, ax2) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [0.5, 3]}, figsize=(10, 8))
        
        extrema['trend'].replace(np.nan, 0.5).loc[start_date:].plot(ax=ax1, title='trend')

        extrema.reset_index(inplace=True)

        # (HH * 1.0).loc[start_date:].plot(ax=ax1, title='trend')
        # ax1.axhline(0, color='green', linestyle='--')
        
        extrema[['Close', maxima_name, minima_name]].loc[start_date:].plot (ax=ax2, title=symbol)
        
        ax1.xaxis.set_major_locator(plt_ticker.MultipleLocator(28))
        ax1.xaxis.set_minor_locator(plt_ticker.MultipleLocator(7))
        ax1.grid(True, linestyle='--', linewidth=1.0, color='gray', which='major')
        ax1.grid(True, linestyle='--', linewidth=0.5, color='gray', which='minor')
        
        ax2.xaxis.set_major_locator(plt_ticker.MultipleLocator(28))
        ax2.xaxis.set_minor_locator(plt_ticker.MultipleLocator(7))
        ax2.grid(True, linestyle='--', linewidth=1.0, color='gray', which='major')
        ax2.grid(True, linestyle='--', linewidth=0.5, color='gray', which='minor')
        
        plt.tight_layout()
        plt.show()


        return extrema['trend'], extrema['trend'].rolling(window=20).mean()


    @staticmethod
    def __get_trend_older(series, order=3):
        extrema = Analysis_Technical.__get_extrema(series, order=order).ffill()

        # plot_data = extrema[['Close', 'maxima', 'minima']].copy()
        # # range = extrema['Close'].max() - extrema['Close'].min()
        # # mid_range = range / 2
        # # mid = extrema['Close'].min() + mid_range
        # # plot_data['trend'] = ((extrema['trend'] + 1)/2 * range) + extrema['Close'].min()
        # # plot_data['mid'] = mid
        # # # plot_data = extrema[['Low', 'minima']].copy()
        # # # plot_data = extrema[['maxima_change', 'minima_change']].copy()

        # Analysis_Technical.__dataframe_plot(plot_data, title='trend')
        # plt.show()

        maxima_name = 'maxima'
        # maxima_name = 'maxima_change'
        minima_name = 'minima'
        # minima_name = 'minima_change'
        # up trend
        extrema.loc[extrema[maxima_name] > extrema[maxima_name].shift(1), 'HH'] = True
        extrema.loc[extrema[maxima_name] < extrema[maxima_name].shift(1), 'HH'] = False
        extrema['HH'] = extrema['HH'].bfill()
        
        extrema.loc[extrema[minima_name] > extrema[minima_name].shift(1), 'HL'] = True
        extrema.loc[extrema[minima_name] < extrema[minima_name].shift(1), 'HL'] = False
        extrema['HL'] = extrema['HL'].bfill()

        extrema['up_trend'] = (extrema['HH'] & extrema['HL']) * 1.0

        # up trend
        extrema.loc[extrema[maxima_name] < extrema[maxima_name].shift(1), 'LH'] = True
        extrema.loc[extrema[maxima_name] > extrema[maxima_name].shift(1), 'LH'] = False
        extrema['LH'] = extrema['LH'].bfill()
        
        extrema.loc[extrema[minima_name] < extrema[minima_name].shift(1), 'LL'] = True
        extrema.loc[extrema[minima_name] > extrema[minima_name].shift(1), 'LL'] = False
        extrema['LL'] = extrema['LL'].bfill()

        extrema['down_trend'] = (extrema['LH'] & extrema['LL']) * -1.0

        # trend
        extrema['trend'] = extrema['up_trend'] + extrema['down_trend']
        extrema['trend_rolling'] = extrema['trend'].rolling(window=20).mean()


        
        plot_data = extrema[['Close']].copy()
        range = extrema['Close'].max() - extrema['Close'].min()
        mid_range = range / 2
        mid = extrema['Close'].min() + mid_range
        plot_data['trend'] = ((extrema['trend_rolling'] + 1)/2 * range) + extrema['Close'].min()
        plot_data['mid'] = mid
        # plot_data = extrema[['Low', 'minima']].copy()
        # plot_data = extrema[['maxima_change', 'minima_change']].copy()

        Analysis_Technical.__dataframe_plot(plot_data, title='trend')
        plt.show()

        return None, None


    @staticmethod
    def __get_trend_oldest(series, order=3):
        extrema = Analysis_Technical.__get_extrema(series, order=order).ffill()
        peaks = extrema['maxima']
        bottoms = extrema['minima']

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

        trend = pd.Series(0.0, index=series.index, name='trend')
        trend.loc[uptrends == 1.0] = 1.0
        trend.loc[downtrends == 1.0] = -1.0

        return trend, trend.rolling(window=20).mean()

    @staticmethod
    def __get_extrema_test(chart, order=3, sigma=0.03):
        high = chart['High']
        low = chart['Low']

        maxima_np = argrelextrema(high[:-1-order].values, np.greater, order=order)
        minima_np = argrelextrema(low[:-1-order].values, np.less, order=order)
        extrema_np = np.sort(np.concatenate([maxima_np, minima_np], axis=1))[0]

        extrema = chart[['Close', 'High', 'Low']].copy()
        extrema['maxima'] = np.nan
        extrema['maxima'].iloc[maxima_np] = high.iloc[maxima_np]
        extrema['minima'] = np.nan
        extrema['minima'].iloc[minima_np] = low.iloc[minima_np]
        # extrema['extrema'] = np.nan
        # extrema['extrema'].iloc[extrema_np] = close.iloc[extrema_np]

        return extrema
    
    @staticmethod
    def __trace(chart_df, symbol):
        plot_data = chart_df[['Close']]
        close = chart_df['Close'].values

        trace.frank_test(close, symbol)

        if False:
            Analysis_Technical.__dataframe_plot(plot_data, title=symbol)
            plt.show()
        
        

    @staticmethod
    def __get_sideways(series):
        extrema = Analysis_Technical.__get_extrema(series)

        extrema_prices = extrema['extrema'].dropna()

        extrema_prices_max = extrema_prices.max()
        extrema_prices_range = extrema_prices_max - extrema_prices.min()

        bandwith = (extrema_prices_max / extrema_prices_range) / 3

        kde = KernelDensity(kernel='gaussian', bandwidth=bandwith).fit(extrema_prices.values.reshape(-1, 1))

        # make a linear interpolation between min and max values with 1000 samples
        # price_range = np.linspace(min(extrema_prices), max(extrema_prices), 1000).reshape(-1, 1)

        
        # score values in price range
        price_range = np.sort(series.values).reshape(-1, 1)
        score = np.exp(kde.score_samples(price_range))

        # score_threshold = score.max() / 2
        # print(score_threshold)

        # price_range_peaks = price_range[score > score_threshold]
        # print(price_range_peaks)

        
        peak = find_peaks(score)[0]
        peak_scores = score[peak]
        peak_prices = price_range[peak]
        score_threshold = ((score.max()-score.min()) * 0.6) + score.min()
        peak_prices_threshold = peak_prices[peak_scores > score_threshold]
        print(peak_prices_threshold)
        plot_data = series.to_frame()
        for price in sorted(peak_prices_threshold):
            print(price[0])
            print(series[series == price[0]])


        # peak_prices = score[peak]





        # # plot it out
        plt.plot(price_range, score)
        # plt.plot(series)
        plt.show()


        return
        extrema = Analysis_Technical.__get_extrema(chart)

        extrema_prices = extrema['extrema'].dropna().values
        initial_price = extrema_prices[0]

        kde = KernelDensity(kernel='gaussian', bandwidth=initial_price/100).fit(extrema_prices.reshape(-1, 1))
        
        a, b = min(extrema_prices), max(extrema_prices)
        price_range = np.linspace(a, b, 1000).reshape(-1, 1)
        pdf = np.exp(kde.score_samples(price_range))

        peaks = find_peaks(pdf)[0]
        peak_prices = price_range[peaks]
        peak_values = pdf[peaks]

        peak_values = sorted(peak_values)
        print(peak_values)

        # plt.plot(price_range, pdf)
        # plt.show()

        
        # test = extrema['maxima'].dropna().diff().cumsum()
        # test.plot()
        # plt.show()

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
        # print(chart)

        trend, trend_mean = Analysis_Technical.__get_trend(chart)
        


        plot_datas = {}
        if True:
            plot_data = chart.to_frame()
            plot_min = chart.min()
            plot_max = chart.max()
            plot_range = plot_max - plot_min
            plot_mid_range = plot_range / 2
            plot_mid = plot_mid_range + plot_min

            plot_data['trend'] = (trend_mean * plot_mid_range) + plot_mid
            # plot_data['mid'] = plot_mid
            
            # plot_data['peaks'] = peaks
            # plot_data['bottoms'] = bottoms
            # plot_data['extrema'] = extrema

            plot_datas['test'] = plot_data
            # plot_datas['test'] = extrema

        return plot_datas

    def test(self):
        plot_datas = {}
        for symbol, chart in self.charts.items():
            # if not symbol in ['LTC']: continue
            # if not symbol in ['ASML']: continue
            # if not symbol in ['APH']: continue
            if not symbol in ['CM']: continue
            # if symbol in ['MVRXX', 'LTC']: continue # LTC has a nan on the Close prices
            print(symbol)

            if True:
                trace.frank_test(chart, symbol)

            if False:
                extrema = Analysis_Technical.__get_extrema(chart, order=3, sigma=0.02)

                daily_date_range = pd.date_range(start=extrema.index[0], end=extrema.index[-1], freq='D')
                plot_data = pd.DataFrame(index=daily_date_range)
                plot_data =  plot_data.merge(extrema, how='left', left_index=True, right_index=True)

                plot_data = plot_data.interpolate()

                columns = [
                    'Close',
                    # 'extrema',
                    'extrema_change',
                ]
                plot_data = plot_data[columns]
                Analysis_Technical.__dataframe_plot(plot_data, title=symbol)
                plt.show()



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
            self.charts = storage.load('at_charts_hourly_%s' % self.id)
        else:
            self.charts = yf.download(self.symbols, period='6mo', interval='1h', auto_adjust=False, group_by='ticker')
            storage.save(self.charts, 'at_charts_hourly_%s' % self.id)
        
        # symbols = self.charts.columns.levels[0]
        # columns = self.charts.columns.levels[1]
        # for symbol in symbols:
        #     chart_symbol = self.charts.loc[:, symbol]
        #     print(chart_symbol)
        #     break
        # for column in columns:
        #     chart_column = self.charts.xs(column, level=1, axis=1)
        #     print(chart_column)
        #     break


    def __set_charts_old(self):
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
