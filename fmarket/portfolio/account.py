import pandas as pd
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
            self.transactions = db.table_read('transactions_%s' % self.id)
            del(db)

    def get_position_symbols(self):
       return sorted(self.positions.index)
    
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
