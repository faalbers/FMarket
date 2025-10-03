
from ..tickers import Tickers
from ..database import Database
import pandas as pd
import numpy as np
import talib as ta

class Analysis():
    def __init__(self, symbols=[]):
        self.db = Database('analysis')
        self.tickers = Tickers(symbols)
        self.__data = {}

    def get_filter(self, update_cache=False):
        symbols = self.tickers.get().index
        if update_cache:
            # cache all symbols first
            self.__cache_filter()
            filter = self.db.table_read('analysis', keys=symbols)
        else:
            # cache only missing data
            filter = self.db.table_read('analysis', keys=symbols)
            missing = set(symbols).difference(filter.index)
            if len(missing) > 0:
                self.__cache_filter(missing)
                filter = self.db.table_read('analysis', keys=symbols)
        return filter

    def __cache_filter(self, symbols=[]):
        pd.options.display.float_format = '{:.3f}'.format
        if len(symbols) == 0:
            tickers = self.tickers
        else:
            tickers = Tickers(symbols)

        # handle info
        print('cache: info')
        self.__data['info'] = tickers.get_info()
        filter =  self.__data['info'].copy(deep=True)

        # name market cap
        market_cap = filter['market_cap'] / 1000000
        filter.loc[market_cap >= 250, 'market_cap_name'] = 'Small'
        filter.loc[market_cap >= 2000, 'market_cap_name'] = 'Mid'
        filter.loc[market_cap >= 10000, 'market_cap_name'] = 'Large'
        filter.loc[market_cap >= 200000, 'market_cap_name'] = 'Mega'

        # handle funds info
        is_fund_overview = filter['fund_overview'].notna()
        filter.loc[is_fund_overview, 'fund_category'] = filter.loc[is_fund_overview, 'fund_overview'].apply(lambda x: x.get('categoryName'))
        filter.loc[is_fund_overview, 'fund_family'] = filter.loc[is_fund_overview, 'fund_overview'].apply(lambda x: x.get('family'))
        filter = filter.drop('fund_overview', axis=1)

        # get minervini
        self.__data['chart'] = tickers.get_chart()
        minervini = self.__get_minervini()
        filter = filter.merge(minervini, how='left', left_index=True, right_index=True)
        
        # get fundamental yearly
        self.__data['fundamental'] = tickers.get_fundamental()
        fundamental_yearly = self.__get_fundamental('yearly')

        # keep market_cap_name as market_cap
        filter.drop('market_cap', axis=1, inplace=True)
        filter.rename(columns={'market_cap_name': 'market_cap'}, inplace=True)

        # fix 'infinity' from info
        for column in filter.columns[filter.apply(lambda x: 'Infinity' in x.values)]:
            filter.loc[filter[column] == 'Infinity', column] = np.nan

        # infer al object columns
        filter = filter.infer_objects()

        # clear data
        self.__data = {}

        # write to db
        self.db.backup()
        self.db.table_write('analysis', filter)

    def __get_minervini(self):
        chart_data = pd.DataFrame()
        for symbol, chart in self.__data['chart'].items():
            # there are some price values that are strings because of Infinity
            chart['adj_close'] = chart['adj_close'].astype(float, errors='ignore')

            # get mark minervini classifications
            # https://www.chartmill.com/documentation/stock-screener/technical-analysis-trading-strategies/496-Mark-Minervini-Trend-Template-A-Step-by-Step-Guide-for-Beginners
            current_price = chart['adj_close'].dropna().iloc[-1]
            chart_data.loc[symbol, 'adj_close'] = current_price

            conditions = []
            
            sma_50 = ta.SMA(chart['adj_close'], timeperiod=50)
            
            for period in [150, 200]:
                if chart.shape[0] >= period:
                    sma = ta.SMA(chart['adj_close'], timeperiod=period)
                    conditions.append(current_price > sma.iloc[-1]) # Current Price Above the period Moving Average
                    conditions.append(sma_50.iloc[-1] > sma.iloc[-1]) # 50-Day Moving Average Above the period Moving Average
                    if chart.shape[0] >= (period + 20):
                        slope = np.polyfit(range(20), sma.iloc[-20:].values, 1)[0]
                        conditions.append(slope > 0.0,) # period Moving Average Increasing during last month
                    else:
                        conditions.append(False)
                else:
                    conditions += [False, False, False]

            if chart.shape[0] >= 52*5:
                low_52_week = chart.iloc[-(52*5)]['low'].min()
                conditions.append(current_price > (low_52_week * 1.3)) # Current Price Above 52-Week Low plus 30%
                high_52_week = chart.iloc[-(52*5)]['high'].max()
                conditions.append(current_price > (high_52_week * 0.75)) # Current Price Above 52-Week High minus 25%
            else:
                conditions += [False, False]

            if chart.shape[0] >= 14:
                rsi = ta.RSI(chart['adj_close'], timeperiod=14).iloc[-1]
                conditions.append(rsi > 70) # RSI Above 70
            else:
                conditions.append(False)

            minervini_score_percent = (np.array([float(x) for x in conditions]) / len(conditions)).sum() * 100.0
            chart_data.loc[symbol, 'minervini_score'] = minervini_score_percent

        return chart_data

    def __get_fundamental(self, period):
        print(self.__data['fundamental'][period])