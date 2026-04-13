import yfinance as yf
from ratelimit import limits, sleep_and_retry
import pandas as pd
import numpy as np
import talib as ta
import matplotlib.pyplot as plt
from ..utils import FTime

class Analysis_Technical():
    def __init__(self, symbols):
        self.last_market_date = FTime().last_market_date
        self.__get_charts(symbols)

    def get_uptrends(self):
        trends = {}
        for symbol, chart in self.charts.items():
            chart_work = chart[['Adj Close']].copy()
            chart_work['date'] = chart.index

            chart_work['cummax'] = chart['Adj Close'].cummax()

            def get_min(group):
                if group.shape[0] <= 10: return
                chart_work.loc[group.index, 'dip'] = group['Adj Close'].min()
            group_HH = chart_work.groupby('cummax')[['Adj Close', 'cummax']].apply(get_min)

            if 'dip' in chart_work.columns:
                # print(symbol)
                chart_work['dip'] = chart_work['dip'].bfill()
                chart_work['dip'] = chart_work['dip'].ffill()
                ll_past = chart_work['dip'].shift(1)
                set_trend = ll_past.notna() & (chart_work['dip'] != ll_past)
                uptrend = chart_work['dip'] > ll_past
                chart_work.loc[set_trend, 'uptrend'] = uptrend

                if chart_work['uptrend'].dropna().shape[0] > 0:
                    chart_work['uptrend'] = chart_work['uptrend'].ffill()
                    # if symbol in ['CWEN','CM']:
                    #     print(chart_work['uptrend'])
                    #     chart_work[['Adj Close', 'dip']].plot(title=symbol)
                    #     plt.show()

            else:
                chart_work['uptrend'] = np.nan



            trends[symbol] = chart_work['uptrend']

        return trends

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
    
    def __get_charts(self, symbols):
        last_market_date = FTime().last_market_date
        symbols = sorted(set(symbols))
        self.charts = {}
        for symbol in symbols:
            self.__get_charts_symbol(symbol)

    def __set_last_marke_date(self):
        ftime = FTime()
