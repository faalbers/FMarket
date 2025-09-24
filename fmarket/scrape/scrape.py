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
        'polygon_news': True,
        'finviz_news': True,
        'yahoof_info': True,
        'yahoof_fundamental': True,
        'yahoof_chart': True,
        'etrade_quote': True,
    }

    def __init__(self):
        pass

    def update(self, status_only=False):
        # remove old scrape.log
        if not status_only and os.path.exists('scrape.log'): os.remove('scrape.log')

        # clear stop
        Stop().clear

        # initialize info and scrapers
        status_all = ''
        scrapers = []

        # add symbols
        if self.settings['symbols']:
            scrapers.append([FMP_Stocklist, []])
            scrapers.append([Polygon_Tickers, []])
        
        # add polygon news
        if self.settings['polygon_news']:
            scrapers.append([Polygon_News, []])

        # get tickers to selectively get symbols
        tickers = Tickers()
        
        # add yahoof info
        if self.settings['yahoof_info']:
            symbols = tickers.get()
            scrapers.append([YahooF_Info, sorted(symbols.index)])

            symbols = tickers.get(yahoof=True)
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
        if self.settings['yahoof_fundamental']:
            symbols = tickers.get(active=True)
            
            # add fund_overview
            if 'type' in symbols:
                # add quarterly equity data
                symbols_equity = symbols[symbols['type'] == 'EQUITY']
                if symbols_equity.shape[0] > 0:
                    scrapers.append([YahooF_Fundamental_Yearly, sorted(symbols_equity.index)]) 
                    scrapers.append([YahooF_Fundamental_Quarterly, sorted(symbols_equity.index)]) 

        # add chart
        if self.settings['yahoof_chart']:
            symbols = tickers.get(yahoof=True) # it's not active because the chart decides if it's active
            scrapers.append([YahooF_Chart, sorted(symbols.index)])
        
        # add finviz news
        if self.settings['finviz_news']:
            symbols = tickers.get(active=True)
            scrapers.append([Finviz_News, sorted(symbols.index)])

        # add etrade quote
        if self.settings['etrade_quote']:
            symbols = tickers.get(active=True)
            scrapers.append([Etrade_Quote, sorted(symbols.index)])

        # collect status info
        for scraper in scrapers:
            status, info = scraper[0]().scrape_status(key_values=scraper[1])
            status_all += info + '\n'
        
        # run scrapers in multi processing
        if not status_only: Scrape_Multi(scrapers)

        return status_all

