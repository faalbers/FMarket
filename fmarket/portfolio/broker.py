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

    def get_accounts(self):
        return self.accounts
    
    def get_symbols(self):
        symbols = set()
        for account_id, account in self.accounts.items(): 
            symbols.update(account.get_symbols())
        return sorted(symbols)
    
    def get_report(self):
        accounts = {}
        for account_id, account in self.accounts.items():
            positions = account.get_positions()
            accounts[account_id] = {
                'id': account_id,
                'description': account.description,
                'positions': positions['positions'],
                'history': positions['history'],
            }
        return accounts