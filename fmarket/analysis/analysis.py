from ..tickers import Tickers
from ..database import Database
import pandas as pd
import numpy as np
import talib as ta

class Analysis():
    def __init__(self, symbols=[], cache=False):
        self.db = Database('analysis')
        if cache: self.__cache_data(symbols)
        self.data = self.db.table_read('analysis', keys=symbols)

    def __cache_data(self, symbols):
        pd.options.display.float_format = '{:.3f}'.format
        tickers = Tickers(symbols)

        # start data with all active symbols
        data = tickers.get(active=True) # get only active symbols

        print('Get Analysis:')
        analysis_data = tickers.get_analysis()
        analysis_data['type'] = data['type']
        
        # add treasury rate 10y
        if not '^TNX' in analysis_data['YahooF_Chart:chart']:
            analysis_data['treasury_rate_10y'] = Tickers(['^TNX']).get_chart()['YahooF_Chart:chart']['^TNX']['price'].iloc[-1]
        else:
            analysis_data['treasury_rate_10y'] = analysis_data['YahooF_Chart:chart']['^TNX']['price'].iloc[-1]

        print(analysis_data)
        
        # merge info
        print('Info:')
        info = analysis_data['YahooF_Info:info']

        # name market cap
        market_cap = info['market_cap'] / 1000000
        info.loc[market_cap >= 250, 'market_cap_name'] = 'Small'
        info.loc[market_cap >= 2000, 'market_cap_name'] = 'Mid'
        info.loc[market_cap >= 10000, 'market_cap_name'] = 'Large'
        info.loc[market_cap >= 200000, 'market_cap_name'] = 'Mega'

        # handle funds info
        is_fund_overview = info['fund_overview'].notna()
        info.loc[is_fund_overview, 'fund_category'] = info.loc[is_fund_overview, 'fund_overview'].apply(lambda x: x.get('categoryName'))
        info.loc[is_fund_overview, 'fund_family'] = info.loc[is_fund_overview, 'fund_overview'].apply(lambda x: x.get('family'))
        info = info.drop('fund_overview', axis=1)

        data = data.merge(info, how='left', left_index=True, right_index=True)

        # fix 'infinity' from info
        for column in data.columns[data.apply(lambda x: 'Infinity' in x.values)]:
            data.loc[data[column] == 'Infinity', column] = np.nan

        # get data derrived from charts
        print('charts:')
        minervini = self.get_minervini(analysis_data)
        data = data.merge(minervini, how='left', left_index=True, right_index=True)

        # infer al object columns
        data = data.infer_objects()

        # keep market_cap_name as market_cap
        data.drop('market_cap', axis=1, inplace=True)
        data.rename(columns={'market_cap_name': 'market_cap'}, inplace=True)

        # return
    
        # write to db
        self.db.backup()
        self.db.table_write('analysis', data)

    def get_minervini(self, analysis_data, symbols=[]):
        chart_data = pd.DataFrame()
        for symbol, chart in analysis_data['YahooF_Chart:chart'].items():
            # there are some price values that are strings because of Infinity
            chart['price'] = chart['price'].astype(float, errors='ignore')

            # get mark minervini classifications
            # https://www.chartmill.com/documentation/stock-screener/technical-analysis-trading-strategies/496-Mark-Minervini-Trend-Template-A-Step-by-Step-Guide-for-Beginners
            current_price = chart['price'].dropna().iloc[-1]
            chart_data.loc[symbol, 'price'] = current_price

            conditions = []
            
            sma_50 = ta.SMA(chart['price'], timeperiod=50)
            
            for period in [150, 200]:
                if chart.shape[0] >= period:
                    sma = ta.SMA(chart['price'], timeperiod=period)
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
                rsi = ta.RSI(chart['price'], timeperiod=14).iloc[-1]
                conditions.append(rsi > 70) # RSI Above 70
            else:
                conditions.append(False)

            minervini_score_percent = (np.array([float(x) for x in conditions]) / len(conditions)).sum() * 100.0
            chart_data.loc[symbol, 'minervini_score'] = minervini_score_percent

        return chart_data
