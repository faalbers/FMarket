import pandas as pd
import numpy as np
from ..database import Database
from ..utils import FTime

class Account:
    def __init__(self, id, description=None, data=None):
        self.id = id
        self.description = description
        self.__positions = pd.DataFrame()
        self.__transactions = pd.DataFrame()
        if isinstance(data, dict):
            self.__update_account(data)
        else:
            db = Database('portfolio')
            self.__positions = db.table_read('positions_%s' % self.id)
            if 'date' in self.__positions.columns:
                self.__positions['date'] = pd.to_datetime(self.__positions['date'], unit='s')
            self.__transactions = db.table_read('transactions_%s' % self.id)
            self.__transactions['date'] = pd.to_datetime(self.__transactions['date'], unit='s')
            self.__check_data_corruption()
            self.__fix_quantity_out()
            del(db)

    def get_symbols(self):
       return sorted(self.__positions.index)
    
    def get_positions(self):
        positions = {
            'positions': self.__get_positions(),
            'history': self.__get_history(),
        }

        return positions

    def get_transactions(self):
        return self.__transactions.copy()

    def __get_history(self):
        history_symbols = {}
        symbols = self.__transactions['security_symbol'].unique()
        for symbol in symbols:
            # get all transactions for symbol
            transactions = self.__transactions[self.__transactions['security_symbol'] == symbol].copy()

            # get transaction history with quantity
            has_no_quantity = transactions['quantity'].isna() | (transactions['quantity'] == 0)
            transactions_quantity = transactions[~has_no_quantity]
            history_quantity = transactions_quantity[['date', 'amount', 'quantity']].copy()

            # add reinvest column
            is_reinvest = transactions_quantity['action'] == 'reinvest'
            history_quantity.loc[is_reinvest, 'reinvest'] = history_quantity.loc[is_reinvest, 'amount']

            # set date as index
            history_quantity.set_index('date', inplace=True)
            history_quantity.index = history_quantity.index.date

            # remove rows where all values are nan
            history_quantity.dropna(axis=0, how='all', inplace=True)

            # rename amount to cost and sum on same dates
            history_quantity.rename(columns={'amount': 'cost'}, inplace=True)
            history_quantity = history_quantity.groupby(history_quantity.index).sum()

            # get transaction history with no quantity
            transactions_no_quantity = transactions[has_no_quantity]
            history_no_quantity = transactions_no_quantity[['date', 'amount']].copy()

            # get dividends
            is_dividend = transactions_no_quantity['action'].isin(['dividend', 'dividend qualified'])
            history_no_quantity.loc[is_dividend, 'dividend'] = history_no_quantity.loc[is_dividend, 'amount']
            
            # get cap gains
            is_cap_gain = transactions_no_quantity['action'].str.startswith('cap gain')
            history_no_quantity.loc[is_cap_gain, 'cap_gain'] = history_no_quantity.loc[is_cap_gain, 'amount']

            # set date as index
            history_no_quantity.set_index('date', inplace=True)
            history_no_quantity.index = history_no_quantity.index.date

            # remove rows where all values are nan
            history_no_quantity.dropna(axis=0, how='all', inplace=True)

            # only keep dividends and cap gains and sum on same dates
            history_no_quantity = history_no_quantity[['dividend', 'cap_gain']]
            history_no_quantity = history_no_quantity.groupby(history_no_quantity.index).sum()

            # merge both history together
            history_quantity = history_quantity.merge(history_no_quantity, how='outer', left_index=True, right_index=True)
            history_quantity.replace(np.nan, 0, inplace=True)
            history_quantity.sort_index(inplace=True)

            history_symbols[symbol] = history_quantity

        return history_symbols
        
    def __get_positions(self):
        # get positions arranged by cost
        positions = self.__positions.sort_values('cost', ascending=False).copy()

        # calculate allocation based on cost
        positions['alloc_%'] = ((positions['cost'] / positions['cost'].sum()) * 100).round(2)
        
        # calculate years we have the positions
        if 'date' in positions.columns:
            now = FTime().now_naive
            positions['years'] = ((now - positions['date']).dt.days / 365.0).round(2)
        
        # set final columns
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
        for description in self.__transactions[self.__transactions['action'] == 'quantity out']['description'].unique():
            quantity_in = self.__transactions[(self.__transactions['action'] == 'quantity in') & (self.__transactions['description'] == description)]
            symbol = quantity_in['security_symbol'].unique()[0]
            quantity_out = self.__transactions[(self.__transactions['action'] == 'quantity out') & (self.__transactions['description'] == description)]
            if quantity_out.index.shape[0] > 0:
                self.__transactions.loc[quantity_out.index, 'security_symbol'] = symbol

    def __check_data_corruption(self):
        if self.id != '151827600': return
        def check_symbol_transactions(group):
            if group.shape[0] > 1:
                print('Corrupted transactions in account %s' % self.id)
                print(self.__transactions.loc[group.index])
                raise ValueError('Corrupted transactions')
        self.__transactions.groupby(['security_symbol', 'description', 'amount']).apply(check_symbol_transactions, include_groups=False)
