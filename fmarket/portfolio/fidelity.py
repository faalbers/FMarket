from .broker import Broker
from .account import Account
import glob
import pandas as pd

class Fidelity(Broker):
    def __init__(self):
        super().__init__('Fidelity')

    def read_accounts(self):
        csv_files = glob.glob('data/fidelity/*.csv')
        for csv_file in csv_files:
            data = pd.read_csv(csv_file)
            end_index = data[data['Account Number'].str.startswith('The data')].index[-1]
            data = data[:end_index]
            name = '%s - %s' % (data['Account Name'].unique()[0], data['Account Number'].unique()[0])
            data = data[['Symbol', 'Cost Basis Total', 'Quantity']]
            data.dropna(subset=['Quantity'], inplace=True)
            data['Cost Basis Total'] = data['Cost Basis Total'].str.replace('$', '')
            data['Cost Basis Total'] = pd.to_numeric(data['Cost Basis Total'], errors='coerce')
            data['price_payed'] = data['Cost Basis Total'] / data['Quantity']
            data = data[['Symbol', 'price_payed', 'Quantity']]
            data.rename(columns={'Symbol': 'symbol', 'Quantity': 'quantity'}, inplace=True)
            data.set_index('symbol', inplace=True)
            self.accounts.append(Account(name, data))
            
