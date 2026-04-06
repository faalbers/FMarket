import pandas as pd
from ..database import Database
from .account import Account

class Broker:

    def __init__(self, name):
        self.name = name
        self.accounts = {}
        db = Database('portfolio')
        accounts = db.table_read('accounts')
        del(db)
        accounts = accounts[accounts['broker'] == name]
        for account_id, account in accounts.iterrows():
            self.accounts[account_id] = Account(account_id, account['description'])

    def get_account_ids(self):
        return sorted(self.accounts)

    def get_account(self, id):
        if id in self.accounts:
            return self.accounts[id]
