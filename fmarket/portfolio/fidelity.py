from .broker import Broker
from .account import Account
import glob, os
import pandas as pd
import numpy as np

class Fidelity():
    name = 'Fidelity'
    transaction_rename = {
        'YOU BOUGHT': 'buy',
        'YOU SOLD': 'sell',
        'LONG-TERM CAP GAIN': 'cap gain dist lt',
        'SHORT-TERM CAP GAIN': 'cap gain dist st',
        'DIVIDEND RECEIVED': 'dividend',
        'REINVESTMENT': 'reinvest',
        'REDEMPTION': 'redemption',
        'TRANSFERRED': 'transfer',
    }
    
    def __init__(self, update=False):
        if update: self.__update_fidelity()

    def __update_fidelity(self):
        csv_files = glob.glob('data/fidelity/test/*.csv')
        data = {}
        for csv_file in csv_files:
            account_id = os.path.basename(csv_file).split('.')[0].split('_')[-1]
            if not account_id in data:
                data[account_id] = {
                    'broker': self.name,
                    'id': account_id,
                }
            
            csv_data = pd.read_csv(csv_file)
            if csv_data.index.dtype.type == np.object_:
                index_cut = csv_data.index.str.startswith('The data and information')
                positions = csv_data.iloc[:list(index_cut).index(True)].copy()
                columns = positions.columns
                test = {columns[i]: columns[i+1] for i in range(columns[1:].shape[0])}
                positions.rename(columns=test, inplace=True)
                positions = positions.dropna(axis=1, how='all')
                data[account_id]['description'] = positions['Account Name'].unique()[0]
                rename_columns = {
                    'Symbol': 'symbol',
                    'Quantity': 'quantity',
                    'Cost Basis Total': 'cost',
                }
                keep_columns = [v for v in rename_columns]
                positions = positions[keep_columns]
                positions.rename(columns=rename_columns, inplace=True)
                positions = positions[~positions['symbol'].str.endswith('**')]
                positions.set_index('symbol', inplace=True)
                positions['cost'] = positions['cost'].str.replace('$', '').astype(float)
                positions['price'] = positions['cost'] / positions['quantity']
                data[account_id]['positions'] = positions
            elif csv_data.index.dtype.type == np.int64:
                # handle transaction
                transactions = csv_data[:csv_data.index[csv_data[csv_data.columns[0]].str.startswith('The data and information')][0]]
                rename_columns = {
                    'Run Date': 'date',
                    'Action': 'description',
                    'Amount ($)': 'amount',
                    'Quantity': 'quantity',
                    'Price ($)': 'price',
                    'Symbol': 'security_symbol',
                }
                keep_columns = [v for v in rename_columns]
                transactions = transactions[keep_columns]
                transactions.rename(columns=rename_columns, inplace=True)
                # transactions['action'] = transactions['description']
                transactions['action'] = None
                for action, action_rename in self.transaction_rename.items():
                    actions_found = transactions['description'].str.startswith(action)
                    if actions_found.any():
                        transactions.loc[actions_found, 'action'] = action_rename
                transactions['date'] =  pd.to_datetime(transactions['date'], format='%m/%d/%Y').apply(lambda x: int(x.timestamp()))
                transactions = transactions[transactions['action'].notnull()]
                
                if not 'transactions' in data[account_id]:
                    data[account_id]['transactions'] = transactions
                else:
                    data[account_id]['transactions'] = pd.concat([data[account_id]['transactions'], transactions])

        for account_id, account_data in data.items():
            # sort by transaction dates and create
            account_data['transactions'] = account_data['transactions'].sort_values('date')
            account_data['transactions'].reset_index(drop=True, inplace=True)
            Account(account_id, data=account_data)
