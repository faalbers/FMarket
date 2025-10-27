from ..vault import Vault
from .scrape_multi import Scrape_Multi
from .scrapers import *
from ..tickers import Tickers
from ..utils import Stop
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

    def __init__(self, symbols=[]):
        self.symbols = symbols

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
            scrapers.append([FMP_Stocklist, [], forced])
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
            # add fund_overview
            if 'type' in symbols:
                # add quarterly equity data
                symbols_equity = symbols[symbols['type'] == 'EQUITY']
                if symbols_equity.shape[0] > 0:
                    scrapers.append([YahooF_Info_Quarterly, sorted(symbols_equity.index), forced]) 

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

