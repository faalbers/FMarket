from .etrade import Etrade
from .fidelity import Fidelity
from ..tickers import Tickers
from ..utils import FTime
from ..scrape import Scrape_GUI
import pandas as pd

class Portfolio:
    brokers = [
        Etrade(),
        Fidelity(),
    ]
    
    def __init__(self):
        pass

    def make_quicken_prices(self, date = None, add_symbols = []):
        ftime = FTime()
        symbols = set()
        for broker in self.brokers:
            for account in broker.accounts:
                symbols.update(account.assets.index.to_list())
        symbols.update(add_symbols)
        symbols = sorted(symbols)
        Scrape_GUI(symbols, settings=['yahoof_chart'])

        tickers = Tickers(symbols)
        charts = tickers.get_chart()

        if isinstance(date, type(None)):
            date = ftime.get_offset(ftime.now_naive, months=-1)
            date = ftime.get_month_end(date)
        else:
            date = ftime.get_date_naive(date)

        dftn = pd.Series()
        for symbol, chart in charts.items():
            price = chart[:date]
            if price.empty: continue
            price = price.iloc[-1]['adj_close']
            dftn[symbol] = price
    
        dftn = dftn.dropna().round(2)
        path = 'Z:\\Quicken\\Quicken_Import_%s.csv' % date.date()
        
        print(dftn)
        print(path)
        dftn.to_csv(path, header=False, sep=',', encoding='utf-8')
    
    def make_gains(self):
        today = FTime().now_naive.date()
        # pd.options.display.float_format = '{:.2f}'.format
        data = pd.read_csv('data/bought/bought.csv', sep=',', encoding='utf-8')
        data['price'] = data[' BUY PRICE '].str.replace('$', '').astype(float)
        data['shares'] = data['SHARES'].astype(float)
        data['cost'] = data['price'] * data['shares']
        print(data)
        symbols = data['SYMBOL'].unique()
        Scrape_GUI(symbols, settings=['yahoof_chart'])
        
        chart = Tickers(symbols).get_chart()
        results = []
        for symbol in symbols:
            if not symbol in chart: continue
            bought = data[data['SYMBOL']==symbol].copy()
            bought['date'] = pd.to_datetime(bought['DATE'], format='%m/%d/%y')
            bought.set_index('date', inplace=True)

            for date, buy in bought.iterrows():
                # calculate total stocksplits
                stock_splits = chart[symbol].loc[date:]['stock_splits']
                stock_splits = stock_splits[stock_splits > 0.0]
                if not stock_splits.empty:
                    stock_splits = stock_splits.cumprod().iloc[-1]
                    bought.loc[date, 'shares_split'] = buy['shares'] * stock_splits
                else:
                    bought.loc[date, 'shares_split'] = buy['shares']
                
                # calculate dividends
                dividends = chart[symbol].loc[date:][['dividends', 'stock_splits']]
                dividends.loc[~(dividends['stock_splits'] > 0.0), 'stock_splits'] = 1.0
                dividends['stock_splits'] = dividends['stock_splits'].cumprod()
                dividends = dividends[dividends['dividends'] > 0.0]
                dividends['dividends_payed'] = buy['shares'] * dividends['stock_splits'] * dividends['dividends']
                bought.loc[date, 'dividends'] = dividends['dividends_payed'].sum()
            
            close = chart[symbol].iloc[-1]['close']
            symbol_data = bought[['cost', 'shares_split', 'dividends']].sum()
            symbol_data['value'] = symbol_data['shares_split'] * close
            symbol_data.name = symbol

            results.append(symbol_data)
        results = pd.DataFrame(results)
        results['market_gain'] = results['value'] - results['cost']
        results['market_gain_%'] = (results['market_gain'] / results['cost']) * 100
        results['dividends_gain_%'] = (results['dividends'] / results['cost']) * 100
        results['total_gain_%'] = (results['market_gain_%'] + results['dividends_gain_%'])
        results.index.name = 'symbol'
        results.reset_index(inplace=True)
        results = results.round(2)
        print(results)

        path = 'Z:\\AMY\\Value_Report_%s.csv' % today
        results.to_csv(path, header=True, sep=',', encoding='utf-8', index=False)

