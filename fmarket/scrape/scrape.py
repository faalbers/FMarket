from ..vault import Vault
from .scrape_multi import Scrape_Multi
from .scrapers import *
from ..tickers import Tickers
from ..utils import Stop, storage
from ..database import Database
import os
from pprint import pp

class Scrape():
    settings = {
        'symbols': True,
        'sp500_index': True,
        'polygon_news': True,
        'finviz_news': True,
        'yahoof_info': True,
        'yahoof_fundamental': True,
        'yahoof_chart': True,
        'etrade_quote': True,
    }

    def __init__(self, symbols=[], settings=[]):
        self.symbols = symbols
        if len(settings) > 0:
            for setting in self.settings:
                if setting in settings:
                    self.settings[setting] = True
                else:
                    self.settings[setting] = False

    def update(self, status_only=False, forced=False):
        # remove old scrape.log
        if not status_only and os.path.exists('scrape.log'): os.remove('scrape.log')

        # clear stop
        Stop().clear

        # initialize info and scrapers
        status_all = ''
        scrapers = []

        # add symbols
        if self.settings['symbols']:
            # scrapers.append([FMP_Stocklist, [], forced])
            scrapers.append([Polygon_Tickers, [], forced])

        # add S&P500index info
        if self.settings['sp500_index']:
            scrapers.append([YahooF_SP500, [], forced])
        
        # add polygon news
        if self.settings['polygon_news']:
            scrapers.append([Polygon_News, [], forced])

        # get tickers to selectively get symbols
        tickers_all = Tickers(symbols=self.symbols, yahoof=False, active=False)
        tickers_yahoof = Tickers(symbols=self.symbols, active=False)
        tickers_active = Tickers(symbols=self.symbols)

        # add yahoof info
        if self.settings['yahoof_info']:
            symbols = tickers_all.get()
            scrapers.append([YahooF_Info, sorted(symbols.index), forced])

            symbols = tickers_yahoof.get()
            # add fund_overview
            if 'type' in symbols:
                symbols_fund = symbols[symbols['type'] == 'MUTUALFUND']
                if symbols_fund.shape[0] > 0:
                    scrapers.append([YahooF_Fund_Overview, sorted(symbols_fund.index), forced]) 
        
            symbols = tickers_active.get()
            # add estimates
            if 'type' in symbols:
                symbols_equity = symbols[symbols['type'] == 'EQUITY']
                if symbols_equity.shape[0] > 0:
                    scrapers.append([YahooF_Estimates, sorted(symbols_equity.index), forced]) 

        # add fundamental
        if self.settings['yahoof_fundamental']:
            symbols = tickers_active.get()
            
            # add fund_overview
            if 'type' in symbols:
                # add quarterly equity data
                symbols_equity = symbols[symbols['type'] == 'EQUITY']
                if symbols_equity.shape[0] > 0:
                    scrapers.append([YahooF_Fundamental_Yearly, sorted(symbols_equity.index), forced]) 
                    scrapers.append([YahooF_Fundamental_Quarterly, sorted(symbols_equity.index), forced]) 

        # add chart
        if self.settings['yahoof_chart']:
            symbols = tickers_yahoof.get() # it's not active because the chart decides if it's active
            scrapers.append([YahooF_Chart, sorted(symbols.index), forced])
        
        # add finviz news
        if self.settings['finviz_news']:
            symbols = tickers_active.get()
            scrapers.append([Finviz_News, sorted(symbols.index), forced])

        # add etrade quote
        if self.settings['etrade_quote']:
            symbols = tickers_active.get()
            scrapers.append([Etrade_Quote, sorted(symbols.index), forced])

        # collect status info
        for scraper in scrapers:
            status, info = scraper[0]().scrape_status(key_values=scraper[1], forced=scraper[2])
            status_all += info + '\n'
        
        # run scrapers in multi processing
        if not status_only: Scrape_Multi(scrapers)

        return status_all

    def get_database_params(self, update=False):
        db_names = set()
        if self.settings['symbols']:
            db_names.add(FMP_Stocklist.db_name)
            db_names.add(Polygon_Tickers.db_name)
        if self.settings['sp500_index']:
            db_names.add(YahooF_SP500.db_name)
        if self.settings['polygon_news']:
            db_names.add(Polygon_News.db_name)
        if self.settings['yahoof_info']:
            db_names.add(YahooF_Info.db_name)
            db_names.add(YahooF_Fund_Overview.db_name)
            db_names.add(YahooF_Estimates.db_name)
        if self.settings['yahoof_fundamental']:
            db_names.add(YahooF_Fundamental_Yearly.db_name)
            db_names.add(YahooF_Fundamental_Quarterly.db_name)
        if self.settings['yahoof_chart']:
            db_names.add(YahooF_Chart.db_name)
        if self.settings['finviz_news']:
            db_names.add(Finviz_News.db_name)
        if self.settings['etrade_quote']:
            db_names.add(Etrade_Quote.db_name)

        params_cached =  storage.load('database/params_all')
        if isinstance(params_cached, type(None)):
            params_cached = {}

        if update:
            db_names_update = sorted(db_names)
        else:
            db_names_update = sorted(db_names.difference(params_cached.keys()))

        table_info = {}
        for db_name in db_names_update:
            table_info[db_name] = {}
            db = Database(db_name)
            for table_name in db.get_table_names():
                print(db_name,':',table_name,'(get)')
                current_info = table_info[db_name]
                sub_names = table_name.split('_')
                count = len(sub_names)
                for sub_name in sub_names:
                    count -= 1
                    if count == 0:
                        if isinstance(current_info, dict):
                            current_info[sub_name] = set(db.get_table_info(table_name)['columns'])
                        elif isinstance(current_info, set):
                            current_info.add(sub_name)
                    else:
                        if not sub_name in current_info:
                            current_info[sub_name] = current_info = {}
                        else:
                            current_info = current_info[sub_name]
        

        def table_info_recurse(data_read, param_name, params_all):
            values = set()
            values_count = 0
            for key, value in data_read.items():
                if isinstance(value, dict):
                    if len(param_name) > 0:
                        param_name_new = param_name + '_' + key
                    else:
                        param_name_new = key
                    table_info_recurse(value, param_name_new, params_all)
                else:
                    if len(param_name) > 0:
                        param_name_value = param_name + '_' + key
                    else:
                        param_name_value = key
                    values.update(value)
                    values_count += 1
            if values_count == 1:
                params_all[param_name_value] = values
                print(param_name_value, values)
            elif values_count > 1:
                params_all[param_name] = values
                print(param_name, values)
        
        params_updated = {}
        for db_name, tables in table_info.items():
            params_updated[db_name] = {}
            print(db_name,':')
            table_info_recurse(tables, '', params_updated[db_name])

        for db_name, tables in params_updated.items():
            params_cached[db_name] = params_updated[db_name]

        storage.save(params_cached, 'database/params_all')

        params_requested = {}
        for db_name in db_names:
            params_requested[db_name] = params_cached[db_name]

        return params_requested

        # storage.save(params_all, 'database/params_all')

        # return params_all

