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

    def update(self, status=False):
        status_all = ''
        # start scrapes
        scrapers = [
            [FMP_Stocklist, []],
            [Polygon_Tickers, []],
        ]
        for scraper in scrapers:
            status, info = scraper[0]().scrape_status(key_values=scraper[1])
            status_all += info + '\n'
        if not status: Scrape_Multi(scrapers)

        # get tickers
        tickers = Tickers().get()
        scrapers = [
            [YahooF_Info, sorted(tickers.index)],
        ]
        for scraper in scrapers:
            status, info = scraper[0]().scrape_status(key_values=scraper[1])
            status_all += info + '\n'
        if not status: Scrape_Multi(scrapers)

        return status_all

