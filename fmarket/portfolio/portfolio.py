from .etrade import Etrade
from .fidelity import Fidelity
from .broker import Broker
from ..database import Database
from ..tickers import Tickers
from ..utils import FTime
from ..scrape import Scrape_GUI
import pandas as pd

class Portfolio:
    
    def __init__(self, update=False):
        self.brokers = {}
        if update:
            Etrade(update=update),
            Fidelity(update=update),
        self.__get_portfolio()

    def get_broker_names(self):
        return sorted(self.brokers)

    def get_broker(self, name):
        if name in self.brokers:
            raise ValueError(f'Broker {name} does not exist')
        return self.brokers[name]

    def get_account_ids(self, broker_name=None):
        if isinstance(broker_name, type(None)):
            account_ids = []
            for broker_name, broker in self.brokers.items():
                account_ids += broker.get_account_ids()
            return account_ids
        else:
            if broker_name in  self.brokers:
                return self.brokers[broker_name].get_account_ids()
            else:
                raise ValueError(f'Broker {broker_name} does not exist')

    def get_accounts(self, broker_name=None):
        if isinstance(broker_name, type(None)):
            accounts = {}
            for broker_name, broker in self.brokers.items():
                accounts.update(broker.get_accounts())
            return accounts
        else:
            if broker_name in self.brokers:
                return self.brokers[broker_name].get_accounts()
            else:
                raise ValueError(f'Broker {broker_name} does not exist')

    def get_symbols(self, broker_name=None):
        symbols = set()
        if isinstance(broker_name, type(None)):
            for broker_name, broker in self.brokers.items():
                symbols.update(broker.get_symbols())
            return sorted(symbols)
        else:
            if broker_name in self.brokers:
                return self.brokers[broker_name].get_symbols()
            else:
                raise ValueError(f'Broker {broker_name} does not exist')
    
    def make_quicken_prices(self, date = None, add_symbols = []):
        ftime = FTime()
        symbols = set()
        for broker_name, broker in self.brokers.items():
            for account_id, account in broker.accounts.items():
                symbols.update(account.get_position_symbols())
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

    def __get_portfolio(self):
        db = Database('portfolio')
        accounts = db.table_read('accounts')
        del(db)
        if accounts.empty: return
        for broker_name in accounts['broker'].unique():
            self.brokers[broker_name] = Broker(broker_name)
