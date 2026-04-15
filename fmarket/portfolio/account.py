import pandas as pd
import numpy as np
from ..database import Database
from ..utils import FTime

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
            'positions': self.__get_positions(),
            'history': {}
        }
        symbols = self.transactions['security_symbol'].unique()
        for symbol in symbols:
            transactions = self.transactions[self.transactions['security_symbol'] == symbol]

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

        return positions

    def __get_positions(self):
        now = FTime().now_naive
        positions = self.positions.sort_values('cost', ascending=False).copy()
        positions['alloc_%'] = ((positions['cost'] / positions['cost'].sum()) * 100).round(2)
        if 'date' in positions.columns:
            positions['years'] = ((now - positions['date']).dt.days / 365.0).round(2)
        positions.rename(columns={'price': 'price_buy'}, inplace=True)
        columns = [c for c in ['alloc_%', 'cost', 'price_buy', 'quantity', 'years'] if c in positions.columns]
        positions = positions[columns]
        return positions

    def __update_account(self, data):
        db = Database('portfolio')
        transactions = data.pop('transactions')
        db.table_write('transactions_%s' % data['id'], transactions, update=False)

        positions = data.pop('positions')
        db.table_write('positions_%s' % data['id'], positions, replace_table=True)

        account = pd.DataFrame([data])
        account.set_index('id', inplace=True)
        db.table_write('accounts', account, update=False)


    def __fix_quantity_out(self):
        # fix quantity out bug
        for description in self.transactions[self.transactions['action'] == 'quantity out']['description'].unique():
            quantity_in = self.transactions[(self.transactions['action'] == 'quantity in') & (self.transactions['description'] == description)]
            symbol = quantity_in['security_symbol'].unique()[0]
            quantity_out = self.transactions[(self.transactions['action'] == 'quantity out') & (self.transactions['description'] == description)]
            if quantity_out.index.shape[0] > 0:
                self.transactions.loc[quantity_out.index, 'security_symbol'] = symbol
