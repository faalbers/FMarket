from .broker import Broker
from .account import Account
from ..database import Database
import glob, os
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

    def __init__(self, update=False):
        if update: self.__update_etrade()

    def __update_etrade(self):
        ftime = FTime()
        
        # add etrade API data
        
        # self.__set_session()
        # accounts = self.__get_accounts()
        # storage.save(accounts, 'etrade_accounts')            
        # self.__close_session()
        accounts = storage.load('etrade_accounts')
    
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
            transactions.reset_index(drop=True, inplace=True)
            data['transactions'] = transactions

            # add account
            Account(account_id, data=data)
        
        # temporarely add csv accounts
        csv_files = glob.glob('data/etrade/test/*.csv')
        data = {}
        for csv_file in csv_files:
            file_type, account_id = os.path.basename(csv_file).split('.')[0].split('_')
            csv_data = pd.read_csv(csv_file, names=[chr(x+65) for x in range(13)])

            if not account_id in data:
                data[account_id] = {
                    'broker': 'Etrade',
                    'id': account_id,
                }
            if file_type == 'PortfolioDownload':
                data[account_id]['description'] = csv_data.loc[2, 'A'].split(' -')[0]
            
            # handle positions
            if file_type == 'PortfolioDownload':
                positions_index = csv_data[csv_data['A'] == 'Symbol'].index[1]
                positions = csv_data.loc[positions_index:]
                positions = positions.dropna(axis=1, how='all')
                positions = positions.set_axis(positions.iloc[0], axis=1)
                positions = positions.loc[:positions.index[positions['Symbol'] == 'CASH'][0]]
                positions = positions.iloc[1:-1]
                rename_columns = {
                    'Symbol': 'symbol',
                    'Quantity': 'quantity',
                    'Price Paid $': 'price',
                }
                keep_columns = [v for v in rename_columns]
                positions = positions[keep_columns]
                positions.rename(columns=rename_columns, inplace=True)
                positions[['quantity', 'price']] = positions[['quantity', 'price']].astype(float)
                positions = positions.infer_objects()
                positions.set_index('symbol', inplace=True)

                data[account_id]['positions'] = positions

            # handle transactions
            elif file_type == 'DownloadTxnHistory':
                transactions_index = csv_data[csv_data['A'] == 'Activity/Trade Date'].index[0]
                transactions = csv_data.loc[transactions_index:]
                transactions_index = transactions[transactions['A'].str.startswith('For all accounts')].index[0]
                transactions = transactions.loc[:transactions_index-1]
                transactions = transactions.dropna(axis=1, how='all')
                transactions = transactions.set_axis(transactions.iloc[0], axis=1)
                transactions = transactions.iloc[1:]
                rename_columns = {
                    'Transaction Date': 'date',
                    'Description': 'description',
                    'Activity Type': 'action',
                    'Amount $': 'amount',
                    'Quantity #': 'quantity',
                    'Price $': 'price',
                    'Symbol': 'security_symbol',
                }
                keep_columns = [v for v in rename_columns]
                transactions = transactions[keep_columns]
                transactions.rename(columns=rename_columns, inplace=True)
                transactions['date'] =  pd.to_datetime(transactions['date'], format='%m/%d/%y').apply(lambda x: int(x.timestamp()))
                transactions['action'] = transactions['action'].apply(lambda x: self.transaction_rename[x])
                float_columns = ['amount', 'quantity', 'price']
                transactions[float_columns] = transactions[float_columns].astype(float)
                transactions = transactions.infer_objects()
                transactions.sort_values(by='date', inplace=True)
                transactions.reset_index(drop=True, inplace=True)

                # reasses values
                is_dividend_reinvest = (transactions['action'] == 'dividend') & (transactions['amount'] < 0)
                transactions.loc[is_dividend_reinvest, 'action'] = 'reinvest'
                transactions.loc[transactions['action'] == 'dividend', 'action'] = 'dividend'
                is_dividend_reinvest = (transactions['action'] == 'dividend qualified') & (transactions['amount'] < 0)
                transactions.loc[is_dividend_reinvest, 'action'] = 'dividend qualified reinvest'
                transactions.loc[transactions['action'] == 'dividend qualified', 'action'] = 'dividend qualified receive'
                transactions = transactions[transactions['action'] != 'unknown']

                data[account_id]['transactions'] = transactions
            
        for account_id, account_data in data.items():
            Account(account_id, data=account_data)

        # else:
        #     db = Database('portfolio')
        #     accounts = db.table_read('accounts')
        #     accounts = accounts[accounts['broker'] == 'Etrade']
        #     for account_id in accounts.index:
        #         self.accounts.append(Account(account_id))

    def __set_session(self):
        etrade = OAuth1Service(
            name="etrade",
            consumer_key=KEYS['ETRADE']['KEY'],
            consumer_secret=KEYS['ETRADE']['SECRET'],
            request_token_url="https://api.etrade.com/oauth/request_token",
            access_token_url="https://api.etrade.com/oauth/access_token",
            authorize_url="https://us.etrade.com/e/t/etws/authorize?key={}&token={}",
            base_url='https://api.etrade.com')

        request_token, request_token_secret = etrade.get_request_token(
            params={"oauth_callback": "oob", "format": "json"})

        authorize_url = etrade.authorize_url.format(etrade.consumer_key, request_token)
        webbrowser.open(authorize_url, new=1)

        code = input("Enter Etrade CODE: ")
        print(code)

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
            print(account_id)
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