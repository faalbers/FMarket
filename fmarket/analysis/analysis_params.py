from pprint import pp

class Analysis_Params():
    def __init__(self):
        pass

    params = {
        'type': {
            'info':
                "Type of a stock",
            'unit': 'string',
            'formula': None,
            'guidance': None,
            'values': [
                'EQUITY',
                'ETF',
                'INDEX',
                'MONEYMARKET',
                'MUTUALFUND',
                'NONE',
            ],
        },
        'sub_type': {
            'info':
"""Polygon.io provides stock type codes, such as CS for Common Stock, that you can retrieve through their Ticker Types API
endpoint. Unlike standard industry classification codes, Polygon.io's ticker types are used to filter and categorize assets
within their own system.""",
            'unit': 'string',
            'formula': None,
            'guidance': None,
            'values': [
                'CS (Common Stock)',
                'PFD (Preferred Stock)',
                'WARRANT (Warrant)',
                'RIGHT (Rights)',
                # 'BOND (Corporate Bond)',
                'ETF (Exchange Traded Fund)',
                'ETN (Exchange Traded Note)',
                'ETV (Exchange Traded Vehicle)',
                'SP (Structured Product)',
                'ADRC (American Depository Receipt Common)',
                # 'ADRP (American Depository Receipt Preferred)',
                # 'ADRW (American Depository Receipt Warrants)',
                # 'ADRR (American Depository Receipt Rights)',
                'FUND (Fund)',
                # 'BASKET (Basket)',
                'UNIT (Unit)',
                # 'LT (Liquidating Trust)',
                'OS (Ordinary Shares)',
                'GDR (Global Depository Receipts)',
                'OTHER (Other Security Type)',
                'NYRS (New York Registry Shares)',
                # 'AGEN (Agency Bond)',
                # 'EQLK (Equity Linked Bond)',
                'ETS (Single-security ETF)',
                'IX (Index)',
            ],
        },
        'sector': {
            'info':
"""A stock sector is a large grouping of companies that operate in the same part of the economy, sorted by their primary business
activities, such as healthcare, technology, energy, or financials. Investors categorize companies into sectors to understand
overall market trends and diversify their portfolios by spreading investments across different economic segments.""",
            'unit': 'string',
            'formula': None,
            'guidance': None,
            'values': [
                'Basic Materials',
                'Communication Services',
                'Consumer Cyclical',
                'Consumer Defensive',
                'Energy',
                'Financial Services',
                'Healthcare',
                'Industrials',
                'Real Estate',
                'Technology',
                'None',
            ],
        },
        'industry': {
            'info':
"""The industry of a stock is its company's primary business activity, determined by where most of its revenue is generated,
which helps group stocks with similar operations and economic characteristics for portfolio diversification and analysis.
By classifying companies into industries and larger sectors, investors can understand how different parts of the economy are
performing and identify risks and opportunities.""",
            'unit': 'string',
            'formula': None,
            'guidance': None,
            'values': [],
        },
        'fund_category': {
            'info':
"""A fund category in mutual funds is a way to classify funds based on their investment strategy, types of assets held,
and investment objectives. Common categories include equity funds (investing in stocks), debt funds
(investing in fixed-income securities), and hybrid funds (a mix of both). These categories help investors understand a
fund's potential risks, returns, and how it aligns with their financial goals.  """,
            'unit': 'string',
            'formula': None,
            'guidance': None,
            'values': [],
        },
        'fund_family': {
            'info':
"""A fund family is a collection of different mutual funds and other investment products, like ETFs, offered by a single
investment management company, such as Vanguard or Fidelity. These funds within the same family share administrative and
operational systems and are overseen by the same company, allowing investors to access a wide range of investment options
and often providing benefits like lower fees, fee-free fund exchanges, and consolidated reporting within a single platform.""",
            'unit': 'string',
            'formula': None,
            'guidance': None,
            'values': [],
        },
        'market_cap': {
            'info':
"""The market capitalization, or market cap, of a stock is the total market value of a company's outstanding shares,
calculated by multiplying the current stock price by the number of shares outstanding. It's a key indicator of a
company's size, which can help investors understand its relative market standing, risk, and growth potential.
For example, a company with 10 million shares outstanding and a stock price of $35 would have a market cap of $350 million.""",
            'unit': 'string',
            'formula': None,
            'guidance': None,
            'values': [
                'Small (250M <-> 2B)',
                'Mid (2B <-> 10B)',
                'Large (10B <-> 200B)',
                'Mega (200B +)',
            ],
        },
        'minervini_score': {
            'info':
"""The Minervini score uses Mark Minervini's "Trend Template" criteria, focusing on stocks in strong uptrends by checking
if the 50-day moving average (MA) is above the 150-day MA, and the 150-day MA is above the 200-day MA. It also requires
the current stock price to be above the 150-day and 200-day MAs and for the price to be within 25% of its 52-week high.
In addition to these technical factors, successful screeners also incorporate fundamental and relative strength (RS) criteria.""",
            'unit': 'value between 0 and 100',
            'formula': None,
            'guidance': None,
            'values': [],
        },
        'margin_of_safety': {
            'info':
"""The margin of safety refers to the difference between a stock's intrinsic value (what it's worth in 10 years based on fundamentals)
and its market cap (what it's currently worth)""",
            'unit': '%',
            'formula': None,
            'guidance': 'Buy above a certain value. Most select 35%. Lower value is more risk.',
            'values': [],
        },
        'current_ratio': {
            'info':
"""Current Ratio is a financial metric used in company statements to assess a company's short-term liquidity,
or its ability to meet its short-term financial obligations with its current assets.
It's a key liquidity ratio found on a company's balance sheet.""",
            'unit': '%',
            'formula': 'current_assets / current_liabilities',
            'guidance': 'Should be 100 or up',
            'values': [],
        },
        'cash_ratio': {
            'info':
"""Cash Ratio is a financial metric used in company statements to assess a company's immediate ability to meet
its short-term debt obligations using only its most liquid assets: cash and cash equivalents. 
This metric assesses if a company can meet its immediate debts using only cash and near-cash assets. 
If it's too high it does not take up enough liabilities for growth and is too conservative""",
            'unit': '%',
            'formula': 'cash_and_cash_equivalents / current_liabilities',
            'guidance': 'Should be between 50 and 100. Lower cant cover short term debt and higher is too conservative',
            'values': [],
        },
        'gross_profit_margin': {
            'info':
"""Gross Profit = Revenue - Cost of Goods Sold
Gross Profit Margin is a fundamental financial metric that gauges a company's profitability and operational efficiency.
It is the percentage of revenue that a company retains after subtracting the direct costs associated with producing or
delivering its goods or services, known as the Cost of Goods Sold (COGS).""",
            'unit': '%',
            'formula': 'gross_profit / total_revenue',
            'guidance': 'Should be 25 or up',
            'values': [],
        },
        'operating_profit_margin': {
            'info':
"""Operating Profit = Gross Profit - Operating Expenses
Operating Profit Margin, also called operating profit margin or return on sales (ROS), is a financial ratio that measures
a company's profitability and operational efficiency. It indicates how much profit a company makes from its
core business operations after deducting the direct and indirect costs associated with those operations,
relative to its total revenue.""",
            'unit': '%',
            'formula': 'operating_income / total_revenue',
            'guidance': 'Should be 25 or up',
            'values': [],
        },
        'profit_margin': {
            'info':
"""Profit = Operating Profit - Interest Expenses
Profit Margin, also called profit margin or return on earnings (ROE), is a crucial financial ratio that indicates how much
profit a company retains for each dollar of revenue generated after accounting for all expenses, including operating costs,
interest, taxes are NOT included. It's a key indicator of a company's overall financial health and operational efficiency.
A higher profit margin generally suggests that a company is managing its costs effectively and generating substantial profits
from its operations.
Conversely, a lower margin may indicate financial struggles, weak pricing strategies, or inefficiencies.""",
            'unit': '%',
            'formula': 'pretax_income / total_revenue',
            'guidance': 'Should be 20 or up',
            'values': [],
        },
        'net_profit_margin': {
            'info':
"""Net Profit = Profit - Taxes
Net Profit Margin is a crucial financial ratio that indicates how much profit a company retains for each dollar of
revenue generated after accounting for all expenses, including operating costs, interest, and taxes. It's a key
indicator of a company's overall financial health and operational efficiency. A higher net profit margin generally
suggests that a company is managing its costs effectively and generating substantial profits from its operations.
Conversely, a lower margin may indicate financial struggles, weak pricing strategies, or inefficiencies.""",
            'unit': '%',
            'formula': 'net_income / total_revenue',
            'guidance': 'Should be 15 or up',
            'values': [],
        },
        'dividend_yields': {
            'info':
"""This is the dividends yield (percentage of amount versus current share price).
Dividends are distributions of a company's earnings to its shareholders. When a company earns a profit, its board of directors
may decide to pay a portion of that profit to its investors as a reward for their investment, rather than reinvesting it all back
into the business.""",
            'unit': '%',
            'formula': None,
            'guidance': None,
            'values': [],
        },
        'pe_forward': {
            'info':
"""The forward P/E ratio, also known as the leading or prospective P/E ratio, is a stock valuation metric that offers a glimpse
into a company's future earnings potential. The forward P/E ratio estimates how much investors are willing to pay for each dollar
of a company's projected future earnings. Unlike the trailing P/E ratio, which uses past earnings data, the forward P/E is
forward-looking and relies on estimates of future earnings, which are typically provided by company management or financial analysts.""",
            'unit': '$ value per $ earnings',
            'formula': None,
            'guidance': "Remember, it is soley based on predicted data. Compare with others in same industry and sector (peers).",
            'values': [],
        },
        'peg': {
            'info':
"""A PEG ratio is a stock valuation metric that divides a company's P/E ratio (the price-to-earnings ratio based actual earnings)
by a historical earnings growth rate, which could be from the last fiscal year
or a multi-year average. It indicates if a stock's current price is justified by its past earnings performance and growth. """,
            'unit': 'around 1.0',
            'formula': None,
            'guidance':
"""
Compare with others in same industry and sector (peers)
    PEG ttm = 1:
        Suggests the stock is fairly valued, where the market price aligns with historical earnings growth
    PEG ttm < 1:
        May indicate the stock is undervalued, offering potential growth at a reasonable price
    PEG ttm > 1:
        Could indicate the stock is overvalued relative to its historical growth, signaling caution.""",
            'values': [],
        },
        'pe': {
            'info':
"""The price-to-earnings (P/E) ratio is a valuation metric that measures a company's current stock price relative
to its actual earnings per share (EPS). So how much $ you pay for $1 earnings.
It's calculated by dividing the current stock price by the company's earnings per share (EPS).
It's also called valuation multiples, or how many years of earnings needed to get back price.""",
            'unit': '$ value per $ earnings',
            'formula': None,
            'guidance':
"""A lower P/E ratio might suggest a stock is undervalued, while a higher ratio could indicate overvaluation.
Compare with others in same industry and sector (peers).""",
            'values': [],
        },
        'pb': {
            'info':
"""The Price-to-Book (P/B) ratio compares a company's market value to its book value (assets minus liabilities),
showing if a stock is trading above or below its net asset value, helping value investors find potentially
undervalued stocks (low P/B) or identify overvalued ones""",
            'unit': 'multiple',
            'formula': 'market_price / book_value_per_share',
            'guidance':
"""Especially useful for asset-heavy industries like banking but less for tech with intangible assets,
with a ratio below 1 often signaling undervaluation.
    P/B < 1: The market values the company less than its net assets; potentially undervalued.
    P/B > 1: The market values the company more than its net assets, reflecting future growth potential or brand strength (like Coca-Cola)""",
            'values': [],
        },
        'ps': {
            'info':
"""The PS Ratio (Price-to-Sales Ratio) is a valuation metric comparing a company's market value to its total revenue,
showing how much investors pay for each dollar of sales.""",
            'unit': 'multiple',
            'formula': 'market_price / total_revenue_per_share',
            'guidance':
"""Especially particularly useful for valuing growth companies or those without profits,
though it must be compared within the same industry (peers).""",
            'values': [],
        },
        'dividend_coverage_ratio': {
            'info':
"""The Dividend Coverage Ratio (DCR) shows how many times a company can pay its current common dividends using its earnings.
It helps investors gauge dividend safety and future stability.""",
            'unit': 'multiple',
            'formula': 'eps / dividend_yields',
            'guidance':
"""a higher ratio (e.g., above 2x) suggests strong sustainability, while below 1.5x can signal risk,
though using actual cash flow (FCFE) offers a more accurate picture than just net income.""",
            'values': [],
        },
    }

    def get_param_info(self, param):
        info = {}

        # find param
        param_found = None
        for param_search in self.params:
            if param.startswith(param_search):
                param_found = param_search
                break
        if param_found is None:
            return info
        
        info['name'] = param
        info['base_name'] = param_found.replace('_', ' ').title()
        for name, data in self.params[param_found].items():
            info[name] = data

        # get suffixes
        info['suffix'] = param.replace(param_found, '')

        # get periodic
        for period in ['yearly', 'quarterly', 'ttm']:
            if period in info['suffix']:
                if 'growth' in info['suffix']:
                    info['periodic'] = f"This is a {period} growth of base parameter {info['base_name']} in %."
                elif 'count' in info['suffix']:
                    info['periodic'] = f"This is the periods count of a {period} trend of base parameter {info['base_name']}."
                elif 'volatility' in info['suffix']:
                    info['periodic'] = f"This is the volatility of a {period} trend of base parameter {info['base_name']} in %."
                elif 'end_month' in info['suffix']:
                    info['periodic'] = f"This is the ending month of a {period} trend of base parameter {info['base_name']}."
                elif 'end_year' in info['suffix']:
                    info['periodic'] = f"This is the ending year of a {period} trend of base parameter {info['base_name']}."
                elif 'peers_industry' in info['suffix']:
                    info['periodic'] = f"This is the last period's median {period} of it's industry peers of base parameter {info['base_name']}"
                elif 'peers_sector' in info['suffix']:
                    info['periodic'] = f"This is the last period's median {period} of it's sector peers of base parameter {info['base_name']}"
                else:
                    info['periodic'] = f"This is the last period's {period} value of base parameter {info['base_name']}"
                if 'periodic' in info:
                    info['periodic'] += '\n\nBase parameter info:'
                break

        if 'deviation' in info['suffix']:
            info['deviation'] = 'This is the deviation percentage between historic and ttm data.'
            info['deviation'] += '\n\nBase parameter info:'
        
        if not 'periodic' in info:
            if 'peers_industry' in info['suffix']:
                info['peers'] = 'This is the median value of its industry peers.'
            elif 'peers_sector' in info['suffix']:
                info['peers'] = 'This is the median value of its sector peers.'

        return info
    
    def get_param_info_message(self, param):
        param_info = self.get_param_info(param)
        message = ''

        if len(param_info) == 0: return message

        # pp(param_info)
        
        message += '%s\n\n' % param_info['name']

        # type explanation
        if 'periodic' in param_info:
            message += 'periodic: ' + param_info['periodic']
            message += '\n\n'
        
        if 'peers' in param_info:
            message += 'peers: ' + param_info['peers']
            message += '\n\n'
        
        if 'deviation' in param_info:
            message += 'deviation: ' + param_info['deviation']
            message += '\n\n'

        # base name info
        message += param_info['base_name']
        
        if param_info['unit'] is not None:
            message += ' ( unit = %s )' % param_info['unit']
        
        message += '\n\n'
        
        message += param_info['info']
        message += '\n\n'
        
        if param_info['formula'] is not None:
            message += 'formula: ' + param_info['formula']
            message += '\n\n'
        
        if param_info['guidance'] is not None:
            message += 'guidance: ' + param_info['guidance']
            message += '\n\n'

        if len(param_info['values']) > 0:
            message += 'values:\n'
            for value in param_info['values']:
                message += '    %s\n' % value

        return message
    
