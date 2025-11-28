
from ..tickers import Tickers
from ..database import Database
from ..utils import utils, FTime
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
import talib as ta

class Analysis():
    def __init__(self, symbols=[]):
        self.db = Database('analysis')
        self.tickers = Tickers(symbols)

    def get_filter_data(self, update_cache=False):
        symbols = self.tickers.get().index
        if update_cache:
            # cache all symbols first
            self.__cache_filter_data()
            filter_data = self.db.table_read('analysis', keys=symbols)
        else:
            # cache only missing data
            filter_data = self.db.table_read('analysis', keys=symbols)
            missing = set(symbols).difference(filter_data.index)
            if len(missing) > 0:
                self.__cache_filter_data(missing)
                filter_data = self.db.table_read('analysis', keys=symbols)
        
        # add additional info data
        filter_data = self.__add_info_data(filter_data)

        # add peers data
        self.__add_peers_data(filter_data)

        return filter_data

    def get_chart(self):
        return self.tickers.get_chart()
    
    def get_news(self):
        return self.tickers.get_news()
    
    def get_chart_sector(self):
        # https://www.sectorspdrs.com/
        # https://www.spglobal.com/spdji/en/index-finder/
        # https://www.barchart.com/stocks/indices/us-sectors

        sectors = {
            'SPY': 'All',
            'XLV': 'Healthcare',
            'XLB': 'Basic Materials',
            'XLK': 'Technology',
            'XLF': 'Financial Services',
            'XLI': 'Industrials',
            'XLRE': 'Real Estate',
            'XLC': 'Communication Services',
            'XLU': 'Utilities',
            'XLE': 'Energy',
            'XLP': 'Consumer Defensive',
            'XLY': 'Consumer Cyclical',
        }
        # others = {
        #     '^NDX': 'NASDAQ-100',
        #     '^NDXT': 'NASDAQ-100 Technology Sector',
        # }
        # sp500 = {
        #     '^SPX': 'S&P 500 INDEX',
        #     '^SP500-10': 'S&P 500 Energy (Sector)',
        #     '^SP500-15': 'S&P 500 Materials (Sector)',
        #     '^SP500-20': 'S&P 500 Industrials (Sector)',
        #     '^SP500-25': 'S&P 500 Consumer Discretionary (Sector)',
        #     '^SP500-30': 'S&P 500 Consumer Staples (Sector)',
        #     '^SP500-35': 'S&P 500 Health Care (Sector)',
        #     '^SP500-40': 'S&P 500 Financials (Sector)',
        #     '^SP500-45': 'S&P 500 Information Technology (Sector)',
        #     '^SP500-50': 'S&P 500 Communication Services (Sector)',
        #     '^SP500-55': 'S&P 500 Utilities (Sector)',
        #     '^SP500-60': 'S&P 500 Real Estate (Sector)',
        # }
        
        tickers = Tickers(sorted(sectors)).get_chart()
        chart_sector = pd.DataFrame()
        for symbol, sector_chart in tickers.items():
            if symbol in tickers:
                chart_sector = chart_sector.merge(sector_chart['adj_close'],
                    how='outer', left_index=True, right_index=True)
                chart_sector.rename(columns={'adj_close': sectors[symbol]}, inplace=True)
        
        return chart_sector

    def get_dividend_yields(self):
        charts = self.tickers.get_catalog('analysis_chart')['YahooF_Chart:chart']
        dividend_yields = self.__get_dividends(charts)['dividend_yields']
        return dividend_yields
    
    def get_fundamentals(self):
        fundamental_data = self.tickers.get_catalog('analysis_fundamental')
        charts = self.tickers.get_catalog('analysis_chart')['YahooF_Chart:chart']
        
        # get fundamentals
        fundamentals = {}
        fundamentals['yearly'] = self.__get_fundamental('yearly', fundamental_data['YahooF_Fundamental_Yearly:yearly'], charts)
        fundamentals['quarterly'] = self.__get_fundamental('quarterly', fundamental_data['YahooF_Fundamental_Quarterly:quarterly'], charts)
        fundamentals['ttm'] = self.__get_fundamental_ttm(fundamental_data['YahooF_Fundamental_Quarterly:ttm'], charts).T

        return fundamentals

    def __cache_filter_data(self, symbols=[]):
        pd.options.display.float_format = '{:.3f}'.format
        if len(symbols) == 0:
            tickers = self.tickers
        else:
            tickers = Tickers(symbols)
        print('update analysis cache on %s symbols' % tickers.count)

        # handle info
        print('get data: info')
        info = tickers.get()
        info = info.merge(
            tickers.get_catalog('analysis_info')['YahooF_Info:info'],
            how='outer', left_index=True, right_index=True)

        # start filter data
        filter_data = info.copy(deep=True)

        # name market cap
        market_cap = filter_data['market_cap'] / 1000000
        filter_data.loc[market_cap >= 250, 'market_cap_name'] = 'Small'
        filter_data.loc[market_cap >= 2000, 'market_cap_name'] = 'Mid'
        filter_data.loc[market_cap >= 10000, 'market_cap_name'] = 'Large'
        filter_data.loc[market_cap >= 200000, 'market_cap_name'] = 'Mega'

        # handle funds info
        is_fund_overview = filter_data['fund_overview'].notna()
        filter_data.loc[is_fund_overview, 'fund_category'] = filter_data.loc[is_fund_overview, 'fund_overview'].apply(lambda x: x.get('categoryName'))
        filter_data.loc[is_fund_overview, 'fund_family'] = filter_data.loc[is_fund_overview, 'fund_overview'].apply(lambda x: x.get('family'))
        filter_data = filter_data.drop('fund_overview', axis=1)

        # handle chart data
        print('get data: chart')
        charts = tickers.get_catalog('analysis_chart')['YahooF_Chart:chart']

        # get history years
        now = FTime().now_naive
        for symbol, chart in charts.items():
            filter_data.loc[symbol, 'history_years'] = int((now - chart.index[0]).days / 365)
        
        # get minervini
        minervini = self.__get_minervini(charts)
        filter_data = filter_data.merge(minervini, how='left', left_index=True, right_index=True)

        # get dividends
        dividends = self.__get_dividends(charts)
        for period in ['yearly', 'ttm']:
            name = 'dividend_yields_'+period
            trends = self.__get_trends(dividends['dividend_yields'][period], name=name)
            period_end_name = name+'_period_end'
            end_period = trends[period_end_name].infer_objects()
            trends.drop(period_end_name, axis=1, inplace=True)
            if period == 'yearly':
                trends[name+'_end_year'] = end_period
            filter_data = filter_data.merge(trends, how='left', left_index=True, right_index=True)

        # handle fundamentals data
        print('get data: fundamental')
        fundamental_data = tickers.get_catalog('analysis_fundamental')
        
        # get fundamentals
        fundamentals = {}
        fundamentals['yearly'] = self.__get_fundamental('yearly', fundamental_data['YahooF_Fundamental_Yearly:yearly'], charts)
        fundamentals['quarterly'] = self.__get_fundamental('quarterly', fundamental_data['YahooF_Fundamental_Quarterly:quarterly'], charts)
        fundamentals['ttm'] = self.__get_fundamental_ttm(fundamental_data['YahooF_Fundamental_Quarterly:ttm'], charts).T

        # get fundamentals trends
        # params_skip = ['free cash flow', 'price to free cash flow']
        params_skip = ['price to free cash flow']
        for period in ['yearly', 'quarterly']:
            for param, trend_data in fundamentals[period].items():
                if trend_data.empty: continue
                if param in params_skip: continue
                name = param.replace(' ', '_')+'_'+period
                if 'quarterly':
                    trends = self.__get_trends(trend_data, name=name, check_gaps=False)
                else:
                    trends = self.__get_trends(trend_data, name=name)
                end_period = trends[name+'_period_end'].infer_objects()
                trends.drop(name+'_period_end', axis=1, inplace=True)
                if period == 'quarterly':
                    trends[name+'_end_year'] = end_period.dt.year
                    trends[name+'_end_month'] = end_period.dt.month
                elif period == 'yearly':
                    trends[name+'_end_year'] = end_period
                filter_data = filter_data.merge(trends, how='left', left_index=True, right_index=True)
        # # remove some fundamentals and just keep trends
        # for param in ['total_revenue', 'free_cash_flow']:
        #     filter_data = filter_data.drop([param+'_yearly', param+'_quarterly'], axis=1)

        # get dividend coverage ratio
        if not dividends['dividend_yields']['ttm'].empty:
            dividend_coverage_ratio = fundamentals['ttm']['eps'] / dividends['dividend_yields']['ttm'].T[0]
            dividend_coverage_ratio.name = 'dividend_coverage_ratio'
            filter_data = filter_data.merge(dividend_coverage_ratio, how='left', left_index=True, right_index=True)

        # merge margin of safety
        margins_of_safety = self._get_margins_of_safety(fundamentals, charts, info)
        filter_data = filter_data.merge(margins_of_safety, how='left', left_index=True, right_index=True)

        # rename ttm parameters and merge
        fundamentals['ttm'].drop('free cash flow', axis=1, inplace=True)
        rename = {c:(c.replace(' ', '_')+'_ttm') for c in fundamentals['ttm'].columns}
        fundamentals['ttm'] = fundamentals['ttm'].rename(columns=rename)
        filter_data = filter_data.merge(fundamentals['ttm'], how='left', left_index=True, right_index=True)

        # clean up filter data

        # keep market_cap_name as market_cap
        filter_data.drop('market_cap', axis=1, inplace=True)
        filter_data.rename(columns={'market_cap_name': 'market_cap'}, inplace=True)

        # fix 'infinity' from info
        for column in filter_data.columns[filter_data.apply(lambda x: 'Infinity' in x.values)]:
            filter_data.loc[filter_data[column] == 'Infinity', column] = np.nan

        # infer al object columns
        filter_data = filter_data.infer_objects()

        # write to db
        self.db.backup()
        self.db.table_write('analysis', filter_data)

    def __add_info_data(self, data):
        tickers = Tickers(sorted(data.index))
        info_add = tickers.get_catalog('info')['YahooF_Info:info']
        
        # fix 'infinity' from info
        for column in info_add.columns[info_add.apply(lambda x: 'Infinity' in x.values)]:
            info_add.loc[info_add[column] == 'Infinity', column] = np.nan

        data = data.merge(info_add, how='left', left_index=True, right_index=True, suffixes=('', '_info'))
        return data

    def __add_peers_data(self, filter_data):
        filter_data_all = self.db.table_read('analysis')
        filter_data_all = self.__add_info_data(filter_data_all)
        peers_params = [
            'pe_ttm',
            'pe_ttm_info',
            'pe_forward',
            'peg_ttm',
            'current_ratio_yearly',
            'gross_profit_margin_yearly',
            'gross_profit_margin_ttm',
            'operating_profit_margin_ttm',
            'net_profit_margin_yearly',
        ]
        peers_types = [
            'sector',
            'industry',
        ]
        for peers_type in peers_types:
            if not peers_type in filter_data_all.columns: continue
            for peers_type_name in filter_data_all[peers_type].dropna().unique():
                peers_data = filter_data_all[filter_data_all[peers_type] == peers_type_name]
                for peers_param in peers_params:
                    if not peers_param in peers_data.columns: continue
                    peers_param_data = peers_data[peers_param].dropna()
                    if peers_param_data.empty: continue
                    median_param = '%s_peers_%s' % (peers_param, peers_type)
                    median = peers_param_data.median()
                    peers_param_data = peers_param_data[peers_param_data.index.isin(filter_data.index)]
                    if peers_param_data.shape[0] > 0:
                        filter_data.loc[peers_param_data.index, median_param] = median
    
    def _get_margins_of_safety(self, fundamentals, charts, info):
        data = pd.DataFrame(columns=['margin_of_safety', 'margin_of_safety_volatility', 'margin_of_safety_deviation'])
        if not 'yearly' in fundamentals: return data
        if not 'free cash flow' in fundamentals['yearly']: return data
        if not 'price to free cash flow' in fundamentals['yearly']: return data
        if fundamentals['yearly']['price to free cash flow'].empty: return data
        if not 'ttm' in fundamentals: return data
        if not 'free cash flow' in fundamentals['ttm'].columns: return data

        # get treasury rate 10y
        if not '^TNX' in charts:
            treasury_rate_10y = Tickers(['^TNX']).get_catalog('analysis_chart')['YahooF_Chart:chart']['^TNX']['adj_close'].iloc[-1]
        else:
            treasury_rate_10y = charts['^TNX']['adj_close'].iloc[-1]

        # get yearly fcf trends
        renames = {
            'volatility': 'margin_of_safety_volatility',
            'step_growth': 'growth',
        }
        mos = utils.get_trends(fundamentals['yearly']['free cash flow'])[list(renames)]
        mos.rename(columns=renames, inplace=True)

        # get other info
        mos['pfcf'] = utils.get_average(fundamentals['yearly']['price to free cash flow'])
        mos['fcf'] = fundamentals['ttm'].loc[mos.index.intersection(fundamentals['ttm'].index), 'free cash flow']
        mos['market_cap'] = info.loc[mos.index.intersection(info.index), 'market_cap']
        mos['pfcf_ttm'] = mos['market_cap'] / mos['fcf']
        mos.dropna(how='any', axis=0, inplace=True)
        mos = mos[(mos['pfcf'] > 0) & (mos['fcf'] > 0)]
        if mos.empty: return data

        # calculate intrinsic value
        discount = (treasury_rate_10y + 3.0) / 100.0 # at least 10y treasury rate + 3%, change to decimal
        years = 10
        years = np.arange(10+1)
        for symbol, row in mos.iterrows():
            year_delta = row['fcf'] * (row['growth']/100.0)
            values = [row['fcf']+(year_delta*y) for y in years]
            # print(values[0], values[-1])

            fcf_growth = pd.Series(values).to_frame('fcf')
            fcf_growth['fcf_dcf'] = fcf_growth['fcf'] / ((1.0 + discount) ** years)
            terminal_value = fcf_growth['fcf_dcf'].iloc[-1] * row['pfcf'] # using exit_multiple
            intrinsic_value = fcf_growth['fcf_dcf'].iloc[:-1].sum() + terminal_value
            margin_of_safety = 1.0-(row['market_cap']/intrinsic_value)
            mos.loc[symbol, 'margin_of_safety'] = margin_of_safety
            deviation = np.abs(row['pfcf']-row['pfcf_ttm']) / max(np.abs(row['pfcf']),np.abs(row['pfcf_ttm']))
            mos.loc[symbol, 'margin_of_safety_deviation'] = deviation

        mos = mos[['margin_of_safety', 'margin_of_safety_deviation']] * 100 # turn into percent values

        return mos

    def __get_trends(self, data, name, check_gaps=True):
        renames = {
            'step_growth': '%s_growth' % name,
            'step_count': '%s_count' % name,
            'volatility': '%s_volatility' % name,
            'last_valid_value': name,
            'last_valid_index': '%s_period_end' % name,
        }
        trends_result = utils.get_trends(data, check_gaps=check_gaps)[list(renames)]
        trends_result.rename(columns=renames, inplace=True)

        return trends_result

    def __get_dividends(self, charts):
        ftime = FTime()
        dividends = {
            'all': [],
        }
        dividend_yields = {
            'all': [],
        }
        now = ftime.now_naive
        for symbol, chart in charts.items():
            chart = chart.copy()
            if 'dividends' in chart.columns:
                is_dividend = chart['dividends'] > 0.0
                if is_dividend.any():
                    # if chart.index[-1] > last_close_time: last_close_time = chart.index[-1]
                    # get dividends
                    dividends_found = chart[is_dividend]['dividends']
                    dividends_found.name = symbol
                    # use close price and not adj_close price to calculate yield so that stock splits are accounted for
                    dividends['all'].append(dividends_found)
                    dividend_yields['all'].append((dividends_found / float(chart['close'].iloc[-1])) * 100)

        # prepare all dividends
        dividends['all'] = pd.DataFrame(dividends['all']).T
        dividends['all'].sort_index(inplace=True)
        dividend_yields['all'] = pd.DataFrame(dividend_yields['all']).T
        dividend_yields['all'].sort_index(inplace=True)

        if not dividends['all'].empty:
            # create yearly
            last_year = ftime.get_offset(ftime.date_local, years=-1).year
            dividends['yearly'] = dividends['all'].groupby(dividends['all'].index.year).sum().loc[:last_year]
            dividends['yearly'].replace(0, np.nan, inplace=True)
            # make first value a nan to avoid first incomplete year
            first_indices = dividends['yearly'].notna().idxmax()
            for col in dividends['yearly'].columns:
                dividends['yearly'].loc[first_indices[col], col] = np.nan
            dividends['yearly'].dropna(how='all', axis=1, inplace=True)
            
            dividend_yields['yearly'] = dividend_yields['all'].groupby(dividend_yields['all'].index.year).sum().loc[:last_year]
            dividend_yields['yearly'].replace(0, np.nan, inplace=True)
            # make first value a nan to avoid first incomplete year
            first_indices = dividend_yields['yearly'].notna().idxmax()
            for col in dividend_yields['yearly'].columns:
                dividend_yields['yearly'].loc[first_indices[col], col] = np.nan
            dividend_yields['yearly'].dropna(how='all', axis=1, inplace=True)

            # create ttm
            dividends['ttm'] = dividends['all'].groupby(dividends['all'].index.map(lambda x: relativedelta(now, x).years)).sum()
            dividends['ttm'].sort_index(ascending=False, inplace=True)
            dividends['ttm'].replace(0, np.nan, inplace=True)
            # make first value a nan to avoid first incomplete year
            first_indices = dividends['ttm'].notna().idxmax()
            for col in dividends['ttm'].columns:
                dividends['ttm'].loc[first_indices[col], col] = np.nan
            dividends['ttm'].dropna(how='all', axis=1, inplace=True)
            
            dividend_yields['ttm'] = dividend_yields['all'].groupby(dividend_yields['all'].index.map(lambda x: relativedelta(now, x).years)).sum()
            dividend_yields['ttm'].sort_index(ascending=False, inplace=True)
            dividend_yields['ttm'].replace(0, np.nan, inplace=True)
            # make first value a nan to avoid first incomplete ttm years
            first_indices = dividend_yields['ttm'].notna().idxmax()
            for col in dividend_yields['ttm'].columns:
                dividend_yields['ttm'].loc[first_indices[col], col] = np.nan
            dividend_yields['ttm'].dropna(how='all', axis=1, inplace=True)

        else:
            dividends['yearly'] = pd.DataFrame()
            dividends['ttm'] = pd.DataFrame()
            dividend_yields['yearly'] = pd.DataFrame()
            dividend_yields['ttm'] = pd.DataFrame()

        return {'dividends': dividends, 'dividend_yields': dividend_yields}

    def __get_minervini(self, charts):
        chart_data = pd.DataFrame()
        for symbol, chart in charts.items():
            # there are some price values that are strings because of Infinity
            if 'adj_close' not in chart.columns: continue
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

    def __get_fundamental_ttm(self, fundamental_data, charts):
        trailing = fundamental_data.copy()

        # add price
        price = pd.Series(name='price')
        for symbol, row in trailing.iterrows():
            if symbol in charts and 'adj_close' in charts[symbol]:
                price[symbol] = charts[symbol]['adj_close'].iloc[-1]
            else:
                price[symbol] = np.nan
        trailing = trailing.merge(price, how='outer', left_index=True, right_index=True)

        data = pd.DataFrame()
        if 'current_liabilities' in trailing.columns:
            if 'current_assets' in trailing.columns:
                data['current ratio'] = (trailing['current_assets'] / trailing['current_liabilities']) * 100
            if 'cash_and_cash_equivalents' in trailing.columns:
                data['cash ratio'] = (trailing['cash_and_cash_equivalents'] / trailing['current_liabilities']) * 100.0
        if 'total_revenue' in trailing.columns:
            data['total revenue'] = trailing['total_revenue']
            if 'gross_profit' in trailing.columns:
                data['gross profit margin'] = (trailing['gross_profit'] / trailing['total_revenue']) * 100
            if 'operating_income' in trailing.columns:
                data['operating profit margin'] = (trailing['operating_income'] / trailing['total_revenue']) * 100
            if 'pretax_income' in trailing.columns:
                data['profit margin'] = (trailing['pretax_income'] / trailing['total_revenue']) * 100
            if 'net_income' in trailing.columns:
                data['net profit margin'] = (trailing['net_income'] / trailing['total_revenue']) * 100
        if 'free_cash_flow' in trailing.columns:
            data['free cash flow'] = trailing['free_cash_flow']
        if 'eps' in trailing.columns:
            data['eps'] = trailing['eps']
            data['pe'] = trailing['price']/trailing['eps']

        # post fix data
        data = data.T
        data = data.infer_objects()
        # values with inf had nan values as deviders
        data = data.replace([np.inf, -np.inf], np.nan)
        # drop symbols and dates where all values are nan
        data.dropna(axis=1, how='all', inplace=True)

        return data
        

    def __get_fundamental(self, period, fundamental_data, charts):
        # prepare dataframes
        data = {
            'current ratio': [],
            'cash ratio': [],
            'gross profit margin': [],
            'operating profit margin': [],
            'profit margin': [],
            'net profit margin': [],
            'return on equity': [],
            'return on assets': [],
            'pe': [],
            'pb': [],
            'ps': [],
            'eps': [],
            'free cash flow': [],
            'price to free cash flow': [],
            'total revenue': [],
        }

        # go through each symbol's dataframe
        for symbol, period_data in fundamental_data.items():
            # prepare dataframe
            symbol_period = period_data.copy()
            symbol_period.dropna(axis=0, how='all', inplace=True)

            # add price to dates
            if symbol in charts:
                for date in symbol_period.index:
                    prices = charts[symbol].loc[:date]
                    if not prices.empty and 'adj_close' in prices.columns:
                        symbol_period.loc[date, 'price'] = prices['adj_close'].iloc[-1]

            # change yearly dates to year
            if period == 'yearly':
                symbol_period.index = symbol_period.index.year
            symbol_period = symbol_period.groupby(symbol_period.index).last() # some have more then one results in a period, strangely

            # calculate ratios as Series
            def add_values(param, symbol, values):
                values.name = symbol
                data[param].append(values)
            if 'current_liabilities' in symbol_period.columns:
                if 'current_assets' in symbol_period.columns:
                    add_values('current ratio', symbol, (symbol_period['current_assets'] / symbol_period['current_liabilities']) * 100)
                if 'cash_and_cash_equivalents' in symbol_period.columns:
                    add_values('cash ratio', symbol, (symbol_period['cash_and_cash_equivalents'] / symbol_period['current_liabilities']) * 100.0)
            if 'total_revenue' in symbol_period.columns:
                add_values('total revenue', symbol, symbol_period['total_revenue'])
                if 'gross_profit' in symbol_period.columns:
                    add_values('gross profit margin', symbol, (symbol_period['gross_profit'] / symbol_period['total_revenue']) * 100)
                if 'operating_income' in symbol_period.columns:
                    add_values('operating profit margin', symbol, (symbol_period['operating_income'] / symbol_period['total_revenue']) * 100)
                if 'pretax_income' in symbol_period.columns:
                    add_values('profit margin', symbol, (symbol_period['pretax_income'] / symbol_period['total_revenue']) * 100)
                if 'net_income' in symbol_period.columns:
                    add_values('net profit margin', symbol, (symbol_period['net_income'] / symbol_period['total_revenue']) * 100)
            if 'net_income' in symbol_period.columns:
                if 'stockholders_equity' in symbol_period.columns:
                    add_values('return on equity', symbol, (symbol_period['net_income'] / symbol_period['stockholders_equity']) * 100)
                if 'total_assets' in symbol_period.columns:
                    add_values('return on assets', symbol, (symbol_period['net_income'] / symbol_period['total_assets']) * 100)
            if 'free_cash_flow' in symbol_period.columns:
                add_values('free cash flow', symbol, symbol_period['free_cash_flow'])
            if 'price' in symbol_period.columns:
                if 'eps' in symbol_period.columns:
                    eps = symbol_period['eps']
                    if period == 'quarterly': eps = eps * 4
                    add_values('pe', symbol, symbol_period['price']/eps)
                if 'shares' in symbol_period.columns:
                    market_cap = symbol_period['price'] * symbol_period['shares']
                    if 'free_cash_flow' in symbol_period.columns:
                        fcf = symbol_period['free_cash_flow']
                        if period == 'quarterly': fcf = fcf * 4
                        add_values('price to free cash flow', symbol, market_cap / fcf)
                    if 'book_value' in symbol_period.columns:
                        add_values('pb', symbol, symbol_period['price']/(symbol_period['book_value']/symbol_period['shares']))
                    if 'total_revenue' in symbol_period.columns:
                        add_values('ps', symbol, symbol_period['price']/(symbol_period['total_revenue']/symbol_period['shares']))
                        

            if 'eps' in symbol_period.columns:
                add_values('eps', symbol, symbol_period['eps'])

        # create dataframe pre parameter
        for parameter, series in data.items():
            data[parameter] = pd.DataFrame(series).T
            # values with inf had nan values as deviders
            data[parameter] = data[parameter].replace([np.inf, -np.inf], np.nan)
            # drop symbols and dates where all values are nan
            data[parameter].dropna(axis=1, how='all', inplace=True)
            # sort index
            data[parameter].sort_index(inplace=True)

        return data
