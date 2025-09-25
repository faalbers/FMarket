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
        'chart': {
            YahooF_Chart: {
                'chart': [
                    ['Adj Close', 'price'],
                ],
            },
        },
        'analysis': {
            YahooF_Info: {
                'info': [
                    ['sectorDisp', 'sector'],
                    ['industryDisp', 'industry'],
                    ['marketCap', 'market_cap'],
                    ['trailingPE', 'pe_ttm'],
                    ['forwardPE', 'pe_forward'],
                    ['trailingPegRatio', 'peg_ttm'],
                    ['fundOverview', 'fund_overview'],
                ],
            },
            YahooF_Chart: {
                'chart': [
                    ['Adj Close', 'price'],
                    ['Low', 'low'],
                    ['High', 'high'],
                ],
            },
        },
    }
