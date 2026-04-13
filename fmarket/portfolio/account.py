import pandas as pd
import numpy as np
from ..database import Database

class Account:
    def __init__(self, id, description=None, data=None):
        self.id = id
        self.description = description
        self.positions = pd.DataFrame()
        self.transactions = pd.DataFrame()
        if isinstance(data, dict):
            self.__update_account(data)
        else:
            db = Database('portfolio')
            self.positions = db.table_read('positions_%s' % self.id)
            if 'date' in self.positions.columns:
                self.positions['date'] = pd.to_datetime(self.positions['date'], unit='s')
            self.transactions = db.table_read('transactions_%s' % self.id)
            self.transactions['date'] = pd.to_datetime(self.transactions['date'], unit='s')
            self.__fix_quantity_out()
            del(db)

    def get_symbols(self):
       return sorted(self.positions.index)
    
    def get_positions(self):
        positions = {
            'positions': self.positions,
            'history': {}
        }
        symbols = self.transactions['security_symbol'].unique()
        for symbol in symbols:
            transactions = self.transactions[self.transactions['security_symbol'] == symbol]
            # if symbol == '912797GG6':
            #     print(self.id)
            #     print(transactions)

            history = transactions[['date', 'amount', 'quantity']].copy()
            is_dividend = transactions['action'].isin(['dividend', 'dividend qualified'])
            history.loc[is_dividend, 'dividend'] = history.loc[is_dividend, 'amount']
            is_cap_gain = transactions['action'].str.startswith('cap gain')
            history.loc[is_cap_gain, 'cap_gain'] = history.loc[is_cap_gain, 'amount']
            is_reinvest = transactions['action'] == 'reinvest'
            history.loc[is_reinvest, 'reinvest'] = history.loc[is_reinvest, 'amount']
            history['distribution'] = history['dividend'].replace(np.nan,0) + history['cap_gain'].replace(np.nan,0)
            history['distribution'] = history['distribution'].replace(0, np.nan)
            history.set_index('date', inplace=True)
            history.index = history.index.date
            history.dropna(axis=0, how='all', inplace=True)
            history = history.groupby(history.index).sum()

            positions['history'][symbol] = history
            
            # history = history.cumsum().ffill()
            # history = history.groupby(history.index).last()

        return positions

    def __update_account(self, data):
        db = Database('portfolio')
        transactions = data.pop('transactions')
        db.table_write('transactions_%s' % data['id'], transactions, replace_table=True)

        positions = data.pop('positions')
        db.table_write('positions_%s' % data['id'], positions, replace_table=True)

        account = pd.DataFrame([data])
        account.set_index('id', inplace=True)
        db.table_write('accounts', account, update=False)

        # self.broker = data['broker']
        # self.description = data['description']
        # self.transactions = transactions
        # self.positions = positions

        # accounts = db.table_read('accounts')
        # if self.id in accounts.index:
        #     info = accounts.loc[self.id]
        #     self.broker = info['broker']
        #     self.description = info['description']
        #     self.transactions = db.table_read('transactions_%s' % self.id)
        #     self.positions = db.table_read('positions_%s' % self.id)
        # else:
        #     raise Exception('Account id not found: %s' % self.id)

    def __fix_quantity_out(self):
        # fix quantity out bug
        for description in self.transactions[self.transactions['action'] == 'quantity out']['description'].unique():
            quantity_in = self.transactions[(self.transactions['action'] == 'quantity in') & (self.transactions['description'] == description)]
            symbol = quantity_in['security_symbol'].unique()[0]
            quantity_out = self.transactions[(self.transactions['action'] == 'quantity out') & (self.transactions['description'] == description)]
            if quantity_out.index.shape[0] > 0:
                self.transactions.loc[quantity_out.index, 'security_symbol'] = symbol
