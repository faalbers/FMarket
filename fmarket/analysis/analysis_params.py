from pprint import pp

class Analysis_Params():
    def __init__(self):
        pass

    params = {
        'current_ratio': {
            'info':
"""Current Ratio is a financial metric used in company statements to assess a company's short-term liquidity,
or its ability to meet its short-term financial obligations with its current assets.
It's a key liquidity ratio found on a company's balance sheet.""",
            'unit': '%',
            'guidance': 'Should be 100 or up',
        },
        'cash_ratio': {
            'info':
"""Cash Ratio is a financial metric used in company statements to assess a company's immediate ability to meet
its short-term debt obligations using only its most liquid assets: cash and cash equivalents. 
This metric assesses if a company can meet its immediate debts using only cash and near-cash assets. 
If it's too high it does not take up enough liabilities for growth and is too conservative""",
            'unit': '%',
            'guidance': 'Should be between 50 and 100',
        },
        'gross_profit_margin': {
            'info':
"""Gross Profit Margin is a fundamental financial metric that gauges a company's profitability and operational efficiency.
It is the percentage of revenue that a company retains after subtracting the direct costs associated with producing or
delivering its goods or services, known as the Cost of Goods Sold (COGS).""",
            'unit': '%',
            'guidance': 'Should be 25 or up',
        },
        'net_profit_margin': {
            'info':
"""Net Profit Margin is a crucial financial ratio that indicates how much profit a company retains for each dollar of
revenue generated after accounting for all expenses, including operating costs, interest, and taxes. It's a key
indicator of a company's overall financial health and operational efficiency. A higher net profit margin generally
suggests that a company is managing its costs effectively and generating substantial profits from its operations.
Conversely, a lower margin may indicate financial struggles, weak pricing strategies, or inefficiencies.""",
            'unit': '%',
            'guidance': 'Should be 15 or up',
        },
        'operating_profit_margin': {
            'info':
"""Operating Profit Margin, also called operating profit margin or return on sales (ROS), is a financial ratio that measures
a company's profitability and operational efficiency. It indicates how much profit a company makes from its
core business operations after deducting the direct and indirect costs associated with those operations,
relative to its total revenue.""",
            'unit': '%',
            'guidance': 'Should be 25 or up',
        },
        'profit_margin': {
            'info':
"""Profit Margin, also called profit margin or return on earnings (ROE), is a crucial financial ratio that indicates how much
profit a company retains for each dollar of revenue generated after accounting for all expenses, including operating costs,
interest, taxes are NOT included. It's a key indicator of a company's overall financial health and operational efficiency.
A higher profit margin generally suggests that a company is managing its costs effectively and generating substantial profits
from its operations.
Conversely, a lower margin may indicate financial struggles, weak pricing strategies, or inefficiencies.""",
            'unit': '%',
            'guidance': 'Should be 20 or up',
        },
        'dividends': {
            'info':
"""A dividend is a distribution of a company's earnings to its shareholders. When a company earns a profit, its board of directors
may decide to pay a portion of that profit to its investors as a reward for their investment, rather than reinvesting it all back
into the business.
""",
            'unit': '%',
        },
    }

    def get_info(self, param):
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
                if 'trend' in info['suffix']:
                    info['periodic'] = f"This is a {period} trend of {info['base_name']}."
                elif 'count' in info['suffix']:
                    info['periodic'] = f"This is the periods count of a {period} trend of {info['base_name']}."
                elif 'volatility' in info['suffix']:
                    info['periodic'] = f"This is the volatility of a {period} trend of {info['base_name']}."
                elif 'end_month' in info['suffix']:
                    info['periodic'] = f"This is the ending month of a {period} trend of {info['base_name']}."
                elif 'end_year' in info['suffix']:
                    info['periodic'] = f"This is the ending year of a {period} trend of {info['base_name']}."
                else:
                    info['periodic'] = f"This is the last period's value of a {period} trend of {info['base_name']}."
                break

        return info
    
    def get_info_message(self, param):
        param_info = self.get_info(param)
        message = ''

        if len(param_info) == 0: return message

        # pp(param_info)
        
        message += '%s\n\n' % param_info['name']

        if 'periodic' in param_info:
            message += 'periodic: ' + param_info['periodic']
            message += '\n\n'

        message += param_info['base_name']
        if 'unit' in param_info:
            message += ' ( unit = %s )' % param_info['unit']
        message += '\n\n'
        
        message += param_info['info']
        message += '\n\n'
        
        if 'guidance' in param_info:
            message += 'guidance: ' + param_info['guidance']
            message += '\n\n'

        

        return message