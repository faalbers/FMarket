from ..scrape.scrapers import *

class Catalog():
    def __init__(self):
        pass

    def get(self, catalog):
        if not catalog in self.catalogs: return {}
        return self.catalogs[catalog]
    
    catalogs = {
        'symbols': {
            FMP_Stocklist: {},
            Polygon_Tickers: {},
        },
        'tickers': {
            FMP_Stocklist: {
                'stocklist': [
                    ['name', 'name'],
                    ['type', 'type'],
                ]},
            Polygon_Tickers: {
                'tickers': [
                    ['name', 'name'],
                    ['type', 'sub_type'],
                ]},
            YahooF_Info: {
                'info': [
                    ['shortName', 'name_short'],
                    ['quoteType', 'type'],
                ],
            },
            YahooF_Chart: {
                'status_db': [
                    ['chart', 'chart'],
                    ['chart_last', 'chart_last'],
                ],
            },
        },
    }
