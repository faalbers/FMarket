from ..vault import Vault
from .scrape_multi import Scrape_Multi
from .scrapers import *
from ..tickers import Tickers
from ..utils import Stop
import os
from pprint import pp

class Scrape():
    scrape_symbols = True
    scrape_news = True
    scrape_yahoof_info = True
    scrape_yahoof_fundamental = True
    scrape_yahoof_chart = True

    def __init__(self):
        self.vault = Vault()

    def update(self, status_only=False):
        # remove old scrape.log
        if not status_only and os.path.exists('scrape.log'): os.remove('scrape.log')

        # clear stop
        Stop().clear

        # initialize info and scrapers
        status_all = ''
        scrapers = []

        # add symbols
        if self.scrape_symbols:
            scrapers.append([FMP_Stocklist, []])
            scrapers.append([Polygon_Tickers, []])
        
        # add news
        if self.scrape_news:
            scrapers.append([Polygon_News, []])

        tickers = Tickers()
        
        # add yahoof info
        if self.scrape_yahoof_info:
            symbols = tickers.get()
            scrapers.append([YahooF_Info, sorted(symbols.index)])

            symbols = Tickers().get_yahoof()
            # add fund_overview
            if 'type' in symbols:
                symbols_fund = symbols[symbols['type'] == 'MUTUALFUND']
                if symbols_fund.shape[0] > 0:
                    scrapers.append([YahooF_Fund_Overview, sorted(symbols_fund.index)]) 
        
                # add quarterly equity data
                symbols_equity = symbols[symbols['type'] == 'EQUITY']
                if symbols_equity.shape[0] > 0:
                    scrapers.append([YahooF_Info_Quarterly, sorted(symbols_equity.index)]) 

        # add fundamental
        if self.scrape_yahoof_fundamental:
            symbols = Tickers().get_yahoof()
            
            # add fund_overview
            if 'type' in symbols:
                # add quarterly equity data
                symbols_equity = symbols[symbols['type'] == 'EQUITY']
                if symbols_equity.shape[0] > 0:
                    scrapers.append([YahooF_Info_Quarterly, sorted(symbols_equity.index)]) 
                    scrapers.append([YahooF_Fundamental_Yearly, sorted(symbols_equity.index)]) 
                    scrapers.append([YahooF_Fundamental_Quarterly, sorted(symbols_equity.index)]) 

        # add chart
        if self.scrape_yahoof_chart:
            symbols = Tickers().get_yahoof()
            
            # add chart
            scrapers.append([YahooF_Chart, sorted(symbols.index)])

        # collect status
        for scraper in scrapers:
            status, info = scraper[0]().scrape_status(key_values=scraper[1])
            status_all += info + '\n'
        
        # run scrapers in multi processing
        if not status_only: Scrape_Multi(scrapers)

        return status_all

