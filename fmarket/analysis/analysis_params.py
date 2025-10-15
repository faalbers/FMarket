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
        for period in ['yearly', 'quarterly']:
            if period in info['suffix']:
                if 'trend' in info['suffix']:
                    info['periodic'] = f"This is a {period} trend."
                elif 'count' in info['suffix']:
                    info['periodic'] = f"This is the periods count of a {period} trend."
                elif 'volatility' in info['suffix']:
                    info['periodic'] = f"This is the volatility of a {period} trend."
                elif 'end_month' in info['suffix']:
                    info['periodic'] = f"This is the ending month of a {period} trend."
                elif 'end_year' in info['suffix']:
                    info['periodic'] = f"This is the ending year of a {period} trend."
                else:
                    info['periodic'] = f"This is the last period's value of a {period} trend."
                break

        return info
    
    def get_info_message(self, param):
        param_info = self.get_info(param)
        message = ''

        if len(param_info) == 0: return message

        # pp(param_info)
        
        # message += param_info['name'] + '\n'
        # message += param_info['suffix'] + '\n'
        message += param_info['base_name']
        if 'unit' in param_info:
            message += ' ( unit = %s )' % param_info['unit']
        message += '\n\n'
        message += param_info['info']
        message += '\n\n'

        if 'periodic' in param_info:
            message += 'periodic: ' + param_info['periodic']
            message += '\n\n'
        

        return message