from ..vault import Vault
from .scrape_multi import Scrape_Multi
from .scrapers import *
from ..tickers import Tickers
from ..utils import Stop
import os
from pprint import pp

class Scrape():
    def __init__(self):
        self.vault = Vault()

    def update(self, status_only=False):
        # remove old scrape.log
        if not status_only and os.path.exists('scrape.log'): os.remove('scrape.log')

        # clear stop
        Stop().clear
        
        status_all = ''
        # start symbols scrapes
        scrapers = [
            [FMP_Stocklist, []],
            [Polygon_Tickers, []],
        ]
        for scraper in scrapers:
            status, info = scraper[0]().scrape_status(key_values=scraper[1])
            status_all += info + '\n'
        if not status_only: Scrape_Multi(scrapers)

        # get yahoof info
        tickers = Tickers().get()
        scrapers = [
            [YahooF_Info, sorted(tickers.index)],
        ]
        for scraper in scrapers:
            status, info = scraper[0]().scrape_status(key_values=scraper[1])
            status_all += info + '\n'
        if not status_only: Scrape_Multi(scrapers)

        # get all other data
        tickers = Tickers().get_yahoof()
        scrapers = [
            [YahooF_Chart, sorted(tickers.index)],
            # [YahooF_Chart, ['ABAX']],
        ]
        for scraper in scrapers:
            status, info = scraper[0]().scrape_status(key_values=scraper[1])
            status_all += info + '\n'
        if not status_only: Scrape_Multi(scrapers)

        return status_all

