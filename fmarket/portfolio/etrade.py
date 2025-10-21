from .broker import Broker
from .account import Account
import glob
import pandas as pd

class Etrade(Broker):
    def __init__(self):
        super().__init__('Etrade')
     
    def read_accounts(self):
        csv_files = glob.glob('data/etrade/*.csv')
        for csv_file in csv_files:
            data = pd.read_csv(csv_file, names=[chr(x+65) for x in range(13)])
            name = data.loc[2, 'A']
            if data.loc[7, 'A'] == 'Symbol/CUSIP':
                end_index = data[data['A'] == 'Cash'].index[-1]
                data = data[8:end_index][['A', 'C', 'F']]
                data.rename(columns={'A': 'symbol', 'C': 'price_payed', 'F': 'quantity'}, inplace=True)
                data.set_index('symbol', inplace=True)
                self.accounts.append(Account(name, data))
            elif data.loc[7, 'A'] == 'Symbol':
                end_index = data[data['A'] == 'CASH'].index[-1]
                data = data[8:end_index][['A', 'F', 'E']]
                data.rename(columns={'A': 'symbol', 'F': 'price_payed', 'E': 'quantity'}, inplace=True)
                data.set_index('symbol', inplace=True)
                self.accounts.append(Account(name, data))

            
