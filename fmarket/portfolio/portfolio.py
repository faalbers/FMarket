from .etrade import Etrade
from .fidelity import Fidelity
from ..tickers import Tickers
from ..utils import FTime
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
        tickers = Tickers(sorted(symbols))
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