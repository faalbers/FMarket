from ..vault import Vault
from .scrape_multi import Scrape_Multi
from .scrapers import *
from pprint import pp

class Scrape():
    def __init__(self):
        self.vault = Vault()

    def update_status(self, key_values=[]):
        scrapers = [
            [FMP_Stocklist, []],
            [Polygon_Tickers, []]
        ]
        for scraper in scrapers:
            status, info = scraper[0]().scrape_status(key_values=scraper[1])
            print(info)

    def update(self, key_values=[]):
        scrapers = [
            [FMP_Stocklist, ['BLAH']],
            [Polygon_Tickers, ['FLO']]
        ]
        scrape_multi = Scrape_Multi(scrapers)
        # scrape_multi.update(['symbols'])
