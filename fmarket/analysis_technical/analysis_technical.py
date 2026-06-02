from ..globals import *
import yfinance as yf
import logging
from ..utils import storage, Plot
from scipy.signal import savgol_filter, find_peaks
import talib as ta
import pandas as pd
import numpy as np
from scipy import stats

from . import ai_code

class Analysis_Technical:
    def __init__(self, symbols, id):
        self.symbols = sorted(set(symbols))
        if len(self.symbols) == 0:
            raise ValueError("No valid symbols provided")
        if len(self.symbols) > 50:
            raise ValueError("Too many symbols provided (max limit is 50)")
        self.id = id
        self.__set_charts()

    def test(self):
        chart_symbols = self.charts.columns.levels[0]
        for symbol in chart_symbols:
            # if not symbol in ['EME']: continue
            # chart = self.charts.loc[:'2026-02-03', symbol].copy()
            chart = self.charts.loc[:, symbol].copy().ffill()
            if chart.dropna().empty: continue

            print(symbol)
            # extrema = Analysis_Technical.__get_extrema(chart)

            # plot = Plot()
            # # plot.plot(chart[['Close']])
            # plot.plot(extrema[['high_filtered', 'low_filtered']], title=symbol)
            # plot.scatter(extrema[['maxima', 'minima']])
            # plot.show()

            # break

            # # plot = Plot(reset_index=True, grid_major=7*5*4, grid_minor=7*5)
            # plot = Plot(size=[2,1], height_ratios=[3,1], reset_index=True, annotate=True)
            # # plot.plot(chart[['Close']], title=symbol, annotate=True)
            # plot.plot(chart[['Close']], title=symbol)
            # plot.scatter(chart[['High']], (1,0), alpha=0.4)
            # plot.scatter(chart[['Low']], (1,0), alpha=0.4)
            # plot.show()

            # ai_code.get_trend(chart)
            # self.__get_trend_slope(chart, symbol)
            trend = self.__get_trend(chart, symbol)

            plot = Plot()
            plot.plot(chart[['Close']], title='%s: %s' % (symbol, trend))
            plot.show()


            # break

    @staticmethod
    def __get_trend(chart, symbol):
        extrema_in = Analysis_Technical.__get_extrema(chart)
        
        # reverse rows
        extrema = extrema_in[::-1].copy()
        extrema = extrema.reset_index(drop=True)
        
        extrema.loc[extrema['maxima'].notna(), 'maxima_count'] = 1
        extrema['maxima_count'] = extrema['maxima_count'].cumsum().ffill()
        
        extrema['maxima'] = extrema['maxima'].ffill()
        extrema['maxima_shift'] = extrema['maxima'].shift(1)
        extrema['is_HH'] = ((extrema['maxima'] < extrema['maxima_shift']) & (extrema['maxima_count'] == 2))
        extrema['is_LH'] = ((extrema['maxima'] > extrema['maxima_shift']) & (extrema['maxima_count'] == 2))
        # print(extrema[['maxima', 'maxima_shift', 'maxima_count', 'is_HH']].head(100))
        
        extrema.loc[extrema['minima'].notna(), 'minima_count'] = 1
        extrema['minima_count'] = extrema['minima_count'].cumsum().ffill()
        
        extrema['minima'] = extrema['minima'].ffill()
        extrema['minima_shift'] = extrema['minima'].shift(1)
        extrema['is_HL'] = ((extrema['minima'] < extrema['minima_shift']) & (extrema['minima_count'] == 2))
        extrema['is_LL'] = ((extrema['minima'] > extrema['minima_shift']) & (extrema['minima_count'] == 2))
        # print(extrema[['minima', 'minima_shift', 'minima_count', 'is_HL']].head(100))

        up_trend = extrema['is_HH'].any() & extrema['is_HL'].any()
        down_trend = extrema['is_LH'].any() & extrema['is_LL'].any()

        if up_trend:
            trend = 'uptrend'
        elif down_trend:
            trend = 'downtrend'
        else:
            trend = 'sideways'
        
        # plot = Plot(reset_index=True)
        # plot.plot(extrema_in[['high_filtered', 'low_filtered']], title=trend)
        # plot.scatter(extrema_in[['maxima']])
        # plot.scatter(extrema_in[['minima']])
        # # plot.plot(extrema[['maxima_count']], [0,0])
        # plot.show()

        return trend
    
    @staticmethod
    def __get_trend_slope(chart, symbol):
        extrema = Analysis_Technical.__get_extrema(chart)
        extrema = extrema.reset_index(drop=True)

        maxima_count = extrema['maxima'].dropna().shape[0]
        print('maxima count:', maxima_count)

        last_dev = None
        last_slope = None
        last_maxima = None
        last_trend_line = None
        devs = []
        for lin_count in list(range(3,maxima_count+1)):
        # for lin_count in list(range(3,7)):

            lin_data = extrema['maxima'].dropna().iloc[-lin_count:]
            x = lin_data.index.values
            y = lin_data.values
            slope, intercept, rvalue, pvalue, stderr = stats.linregress(x, y)
            lin_reg = intercept + slope * extrema.index

            work_data = pd.DataFrame(index=extrema.index)
            work_data['trend_line'] = lin_reg
            work_data['maxima'] = lin_data
            work_data['trend_line_flat'] = lin_reg[-1]
            work_data['maxima_line_fit'] = work_data['maxima'] + (-lin_reg + lin_reg[-1])

            dev = (work_data['maxima_line_fit'].std() / work_data['maxima'].mean()) * 100
            devs.append(dev)

            # plot = Plot(size=[2,1])
            # # plot.plot(plot_data[['trend_line']], title='fit: % s, stder: % s' % (fit, dev))
            # plot.plot(work_data[['trend_line']], [0,0])
            # plot.scatter(work_data[['maxima']], [0,0])
            # plot.plot(work_data[['trend_line_flat']], [1,0], title='dev: % s' % dev)
            # plot.scatter(work_data[['maxima_line_fit']], [1,0])
            # plot.show()

            if not isinstance(last_dev, type(None)):
                dev_diff = dev / last_dev
                slope_diff = abs((last_slope - slope) / last_slope)
                print(dev_diff, slope_diff)
                if dev_diff > 3: break

            last_dev = dev
            last_slope = slope
            last_maxima = work_data[['maxima']].copy()
            last_trend_line = work_data[['trend_line']].copy()

        for dev in devs:
            print('%.2f' % dev)
        plot_data = extrema[['maxima', 'high_filtered']].copy()
        plot = Plot()
        plot.plot(plot_data[['high_filtered']], alpha=0.5, title=symbol)
        plot.scatter(plot_data[['maxima']], alpha=0.5)
        plot.scatter(last_maxima)
        plot.plot(last_trend_line)
        plot.show()

        return

    @staticmethod
    def __get_extrema(chart,
            window_length = 49,
            polyorder = 5,
            prominence_mult = 0.5
            ):
        extrema = chart[['Close', 'High', 'Low']].copy().ffill().bfill()
        
        atr_window = 14
        atr_rolling_window = 30
        atr = ta.ATR(extrema['High'].values, extrema['Low'].values, extrema['Close'].values, timeperiod=atr_window)
        atr = ta.SMA(atr, timeperiod=atr_rolling_window)
        prominence = atr * prominence_mult

        high_filtered = savgol_filter(extrema['High'],
            window_length=window_length,
            polyorder=polyorder)
        peaks, _ = find_peaks(high_filtered,
            distance = 15, # Minimum horizontal sample distance between peaks
            prominence=prominence, # minimum distance between top value and highest dip on both sides
        )
        extrema['maxima'] = np.nan
        extrema['maxima'].iloc[peaks] = high_filtered[peaks]

        low_filtered = savgol_filter(extrema['Low'], window_length=window_length, polyorder=polyorder)
        dips, _ = find_peaks(-low_filtered,
            distance = 15, # Minimum horizontal sample distance between peaks
            prominence=prominence, # minimum distance between top value and highest dip on both sides
        )
        extrema['minima'] = np.nan
        extrema['minima'].iloc[dips] = low_filtered[dips]
        extrema['extrema'] = extrema['maxima'].combine_first(extrema['minima'])
        extrema['high_filtered'] = high_filtered
        extrema['low_filtered'] = low_filtered

        return extrema
    
    def __set_charts(self):
        # make yfinance non verbose
        yflogger = logging.getLogger('yfinance')
        yflogger.disabled = True
        yflogger.propagate = False

        
        if USE_CACHE_DATA:
        # if False:
            self.charts = storage.load('at_charts_%s' % self.id)
        else:
            self.charts = yf.download(self.symbols, period='6mo', interval='1h', auto_adjust=False, group_by='ticker')
            storage.save(self.charts, 'at_charts_%s' % self.id)
