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
                    ['Adj Close', 'adj_close'],
                    ['Close', 'close'],
                    ['Low', 'low'],
                    ['High', 'high'],
                    ['Dividends', 'dividends'],
                    ['Stock Splits', 'stock_splits'],
                ],
            },
        },
        'info': {
            YahooF_Info: {
                'info': [
                    ['trailingPE', 'pe_ttm'],
                    ['forwardPE', 'pe_forward'],
                    ['trailingPegRatio', 'peg_ttm'],
                ],
            },
        },
        'analysis_info': {
            YahooF_Info: {
                'info': [
                    ['sectorDisp', 'sector'],
                    ['industryDisp', 'industry'],
                    ['marketCap', 'market_cap'],
                    # ['trailingPE', 'pe_ttm'],
                    # ['forwardPE', 'pe_forward'],
                    # ['trailingPegRatio', 'peg_ttm'],
                    ['fundOverview', 'fund_overview'],
                ],
            },
        },
        'analysis_chart': {
            YahooF_Chart: {
                'chart': [
                    ['Adj Close', 'adj_close'],
                    ['Close', 'close'],
                    ['Low', 'low'],
                    ['High', 'high'],
                    ['Dividends', 'dividends'],
                    # ['Stock Splits', 'stock_splits'],
                ],
            },
        },
        'analysis_chart': {
            YahooF_Chart: {
                'chart': [
                    ['Adj Close', 'adj_close'],
                    ['Close', 'close'],
                    ['Low', 'low'],
                    ['High', 'high'],
                    ['Dividends', 'dividends'],
                    # ['Stock Splits', 'stock_splits'],
                ],
            },
        },
        'analysis_fundamental': {
            YahooF_Fundamental_Quarterly: {
                'ttm': [
                    # Income Statement
                    ['TotalRevenue', 'total_revenue'],
                    ['GrossProfit', 'gross_profit'],
                    ['OperatingIncome', 'operating_income'],
                    ['PretaxIncome', 'pretax_income'],
                    ['NetIncome', 'net_income'],
                    ['DilutedEPS', 'eps'],
                    # ['DilutedAverageShares', 'shares'],
                    ['OrdinarySharesNumber', 'shares'],

                    # Balance Sheet
                    ['CurrentAssets', 'current_assets'],
                    ['TotalAssets', 'total_assets'],
                    ['CurrentLiabilities', 'current_liabilities'],
                    ['CashAndCashEquivalents', 'cash_and_cash_equivalents'],
                    ['StockholdersEquity', 'stockholders_equity'],

                    # Cash Flow Statement
                    ['FreeCashFlow', 'free_cash_flow'],
                ],
                'quarterly': [
                    # Income Statement
                    ['TotalRevenue', 'total_revenue'],
                    ['GrossProfit', 'gross_profit'],
                    ['OperatingIncome', 'operating_income'],
                    ['PretaxIncome', 'pretax_income'],
                    ['NetIncome', 'net_income'],
                    ['DilutedEPS', 'eps'],
                    # ['DilutedAverageShares', 'shares'],
                    ['OrdinarySharesNumber', 'shares'],

                    # Balance Sheet
                    ['CurrentAssets', 'current_assets'],
                    ['TotalAssets', 'total_assets'],
                    ['CurrentLiabilities', 'current_liabilities'],
                    ['CashAndCashEquivalents', 'cash_and_cash_equivalents'],
                    ['StockholdersEquity', 'stockholders_equity'],
                    ['TangibleBookValue', 'book_value'],

                    # Cash Flow Statement
                    ['FreeCashFlow', 'free_cash_flow'],
                ],
            },
            YahooF_Fundamental_Yearly: {
                'yearly': [
                    # Income Statement
                    ['TotalRevenue', 'total_revenue'],
                    ['GrossProfit', 'gross_profit'],
                    ['OperatingIncome', 'operating_income'],
                    ['PretaxIncome', 'pretax_income'],
                    ['NetIncome', 'net_income'],
                    ['DilutedEPS', 'eps'],
                    # ['DilutedAverageShares', 'shares'],
                    ['OrdinarySharesNumber', 'shares'],

                    # Balance Sheet
                    ['CurrentAssets', 'current_assets'],
                    ['TotalAssets', 'total_assets'],
                    ['CurrentLiabilities', 'current_liabilities'],
                    ['CashAndCashEquivalents', 'cash_and_cash_equivalents'],
                    ['StockholdersEquity', 'stockholders_equity'],
                    ['TangibleBookValue', 'book_value'],
                    

                    # Cash Flow Statement
                    ['FreeCashFlow', 'free_cash_flow'],
                ],
            },
        },
    }
