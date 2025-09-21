from .fmp import FMP
from ....database import Database
from ....utils import FTime
from datetime import datetime
import logging
import pandas as pd

class FMP_Stocklist(FMP):
    db_name = 'fmp_stocklist'

    def __init__(self):
        super().__init__()
        self.db = Database(self.db_name)

    def scrape_data(self, key_values=[]):
        # check status
        status, info = self.scrape_status(key_values=key_values)
        if not status: return

        # create logger with at least 20 character logger name
        self.logger = logging.getLogger('FMP_Stocklist'.ljust(25, ' '))

        self.logger.info('start update')
        
        # backup first
        self.logger.info(self.db.backup())

        request_arguments = {
            'url': 'https://financialmodelingprep.com/api/v3/stock/list',
            # 'params': {},
            'timeout': 30,
        }
        self.request(request_arguments)
        
        # update status
        ftime = FTime()
        status_db = pd.DataFrame([{'timestamp': int(ftime.now_local.timestamp())}], index=['stocklist'])
        status_db.index.name = 'table_name'
        self.db.table_write('status_db', status_db)

        self.logger.info('update done')

    def push_api_data(self, response_data):
        write_data =  []
        write_symbols = []
        exchange_us = ['NYSE', 'NASDAQ', 'PNK', 'OTC', 'AMEX', 'CBOE']
        for entry in response_data:
            if not entry['exchangeShortName'] in exchange_us: continue
            symbol = entry.pop('symbol').upper()
            write_data.append(entry)
            write_symbols.append(symbol)
        
        write_data = pd.DataFrame(write_data, index=write_symbols)
        write_data.index.name = 'symbol'
        self.db.table_write('stocklist', write_data, replace=True)

    def scrape_status(self, key_values=[], tabs=0):
        # get timestamps
        ftime = FTime()
        now = ftime.now_local

        status_db = self.db.table_read('status_db')
        tabs_string = '  '*tabs
        info = '%sdatabase: %s\n' % (tabs_string, self.db_name)
        info += '%s  table: stocklist\n' % (tabs_string)
        status = None
        if status_db.shape[0] > 0:
            last_ts = status_db.loc['stocklist', 'timestamp']
            last_time = ftime.get_from_ts_local(last_ts)
            next_time = ftime.get_offset(last_time, months=6)
            status = now >= next_time
            info += '%s    last update: %s\n' % (tabs_string, last_time)
            info += '%s    next update: %s\n' % (tabs_string, next_time)
        else:
            status = True
            info += '%s    update     : Not scraped before\n' % (tabs_string)
        
        info += '%s    update     : %s\n' % (tabs_string, status)
        
        return status, info
    
    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'stocklist':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.db.table_read('stocklist', keys=key_values, columns=column_names)
                data = data.rename(columns={x[0]: x[1] for x in columns})
                return (data, self.db.timestamp)
            else:
                data = self.db.table_read('stocklist', keys=key_values)
                return (data, self.db.timestamp)

    def get_vault_status(self, key_values, tabs=0):
        status, info = self.scrape_status(tabs=tabs)
        return info
