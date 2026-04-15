from .broker import Broker
from .account import Account
from ..database import Database
import psutil
import pandas as pd
import numpy as np
from rauth import OAuth1Service
import webbrowser
from ratelimit import limits, sleep_and_retry
from data.keys import KEYS
from ..utils import FTime, storage


class Etrade():
    db_name = 'portfolio'
    transaction_rename = {
        'Bought': 'buy',
        'Sold': 'sell',
        'Dividend': 'dividend',
        'Qualified Dividend': 'dividend qualified',
        'Interest': 'unknown',
        'Interest Income': 'unknown',
        'LT Cap Gain Distribution': 'cap gain dist lt',
        'ST Cap Gain Distribution': 'cap gain dist st',
        'Transfer': 'unknown',
        'Online Transfer': 'unknown',
        'Service Fee': 'unknown',
        'Exchange Delivered Out': 'quantity out',
        'Exchange Received In': 'quantity in',
        'Reorganization': 'redemption',
        'Adjustment': 'unknown',
        'MISC': 'unknown',
        'Contribution': 'unknown',
    }

    def __init__(self, key_name, update=False):
        self.key_name = key_name
        if update: self.__update_etrade()

    def __update_etrade(self):
        ftime = FTime()
        
        # add etrade API data
        
        self.__set_session()
        accounts = self.__get_accounts()
        # storage.save(accounts, 'etrade_accounts_%s' % self.key_name)            
        self.__close_session()
        # accounts = storage.load('etrade_accounts_%s' % self.key_name)
    
        for account_id, account_data in accounts.items():
            data = {
                'broker': 'Etrade',
                'id': account_id,
                'description': account_data['info']['accountDesc'],
            }

            # add positions
            positions = {}
            for position in account_data['portfolio']['Position']:
                id = position['positionId']
                product = position['Product']
                position = {
                    'date': int(position['dateAcquired']/1000),
                    'symbol': product['symbol'],
                    'security_type': product['securityType'],
                    'security_type_code': product['productId']['typeCode'],
                    'quantity': position['quantity'],
                    'price': position['pricePaid'],
                    'cost': position['totalCost'],
                    'type': position['positionType'],
                }
                positions[id] = position

            positions = pd.DataFrame(positions).T
            positions = positions.infer_objects()
            positions.sort_values(by='date', inplace=True)
            positions.set_index('symbol', inplace=True)
            data['positions'] = positions

            # add transactions
            transactions = {}
            for transaction_id, transaction_data in account_data['transactions'].items():
                brokerage = transaction_data['brokerage']
                transaction = {
                    'date': int(transaction_data['transactionDate']/1000),
                    'description': transaction_data['description'],
                    'action': self.transaction_rename[transaction_data['transactionType']],
                    'amount': transaction_data['amount'],
                    'quantity': float(brokerage['quantity']),
                    'price': float(brokerage['price']),
                }
                if transaction['action'] == 'unknown': continue
                
                product = brokerage['product']
                if len(product) > 0:
                    transaction['security_symbol'] = product['symbol']
                    transaction['security_type'] = product['securityType']

                # reasses values
                if transaction['action'] in ['dividend', 'dividend qualified']:
                    action = transaction['action']
                    if transaction['amount'] < 0:
                        transaction['action'] = 'reinvest'

                transactions[transaction_id] = transaction
            
            transactions = pd.DataFrame(transactions).T
            transactions = transactions.infer_objects()
            transactions = transactions.replace(0.0, np.nan)
            transactions.sort_values(by='date', inplace=True)
            transactions.index.name = 'id'

            data['transactions'] = transactions

            # create account in database
            Account(account_id, data=data)

    @staticmethod
    def __close_browser():
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'AvastBrowser.exe':
                input('Close Avast Browser !')
                Etrade.__close_browser()
                break
    
    def __set_session(self):
        Etrade.__close_browser()
        
        etrade = OAuth1Service(
            name="etrade",
            consumer_key=KEYS['ETRADE']['KEY%s' % self.key_name],
            consumer_secret=KEYS['ETRADE']['SECRET%s' % self.key_name],
            request_token_url="https://api.etrade.com/oauth/request_token",
            access_token_url="https://api.etrade.com/oauth/access_token",
            authorize_url="https://us.etrade.com/e/t/etws/authorize?key={}&token={}",
            base_url='https://api.etrade.com')

        request_token, request_token_secret = etrade.get_request_token(
            params={"oauth_callback": "oob", "format": "json"})

        authorize_url = etrade.authorize_url.format(etrade.consumer_key, request_token)
        print('Login as Etrade user %s !' % self.key_name)
        webbrowser.open(authorize_url, new=1)

        code = input("Enter Etrade CODE: ")

        self.session = etrade.get_auth_session(request_token,
            request_token_secret,
            params={"oauth_verifier": code})

    def __close_session(self):
        self.session.get('https://api.etrade.com/oauth/revoke_access_token')

    @sleep_and_retry
    @limits(calls=2, period=1)
    def __session_request(self, arguments):
        response = self.session.get(**arguments)
        if response.headers.get('content-type').startswith('application/json'):
            return response.json()
        else:
            print('Non json returned !')
            print(response)

    def __get_accounts(self):
        ftime = FTime()
        end = ftime.date_local
        start = ftime.get_offset(end, months=-((12*3)))
        accounts = {}

        request_arguments = {
            'url': 'https://api.etrade.com/v1/accounts/list.json',
        }
        response = self.__session_request(request_arguments)

        if 'AccountListResponse' in response:
            data = response['AccountListResponse']
            for account in data['Accounts']['Account']:
                account_id = account.pop('accountId')
                if account['accountStatus'] != 'ACTIVE': continue
                accounts[account_id] = {'info': account}

        for account_id, account_data in accounts.items():
            account_id_key = account_data['info']['accountIdKey']

            # get portfolio
            request_arguments = {
                'url': 'https://api.etrade.com/v1/accounts/%s/portfolio.json' % account_id_key,
            }
            response = self.__session_request(request_arguments)
            account_data['portfolio'] = response['PortfolioResponse']['AccountPortfolio'][0]

            # get transactions
            transactions = account_data['transactions'] = {}
            request_arguments = {
                'url': 'https://api.etrade.com/v1/accounts/%s/transactions.json' % account_id_key,
                'params': {
                    'startDate': start.strftime('%m%d%Y'),
                    'endDate': end.strftime('%m%d%Y'),
                    # 'count': '5',
                },
            }

            do_next = True
            while do_next:
                response = self.__session_request(request_arguments)
                response_data = response['TransactionListResponse']
                for transaction in response_data.pop('Transaction'):
                    transaction_id = transaction.pop('transactionId')
                    transactions[transaction_id] = transaction

                if 'marker' in response_data:
                    request_arguments['params']['marker'] = response_data['marker']
                else:
                    do_next = False

        return accounts