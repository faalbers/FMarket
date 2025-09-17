from .polygon import Polygon
from ....database import Database
from ....utils import FTime
from datetime import datetime
import logging
import pandas as pd

class Polygon_Tickers(Polygon):
    db_name = 'polygon_tickers'

    def __init__(self):
        super().__init__()
        self.db = Database(self.db_name)

    def scrape_data(self, key_values=[]):
        # check status
        status, info = self.scrape_status(key_values=key_values)
        if not status: return

        self.logger = logging.getLogger('Polygon_Tickers'.ljust(20, ' '))

        self.logger.info('start update')
        
        # backup first
        self.logger.info(self.db.backup())

        # get tickers
        request_arguments = {
            'url': 'https://api.polygon.io/v3/reference/tickers',
            'params': {
                'limit': 1000,
            },
        }

        self.request(request_arguments, self.push_tickers_data)

        # get types
        request_arguments = {
                'url': 'https://api.polygon.io/v3/reference/tickers/types',
        }

        self.request(request_arguments, self.push_types_data)

        # update status
        ftime = FTime()
        status_db = pd.DataFrame([{'timestamp': int(ftime.now_local.timestamp())}], index=['tickers'])
        status_db.index.name = 'table_name'
        self.db.table_write('status_db', status_db)

        self.logger.info('update done')

    def push_tickers_data(self, response_data):
        write_data =  []
        write_symbols = []
        for entry in response_data:
            # do not include these markets
            if entry['market'] in ['fx', 'crypto']: continue
            symbol = entry.pop('ticker').upper()

            # create correct ticker symbol
            if entry['market'] == 'stocks' and not symbol.isalpha() and 'type' in entry:
                if 'type' in entry and entry['type'] == 'UNIT':
                    # handle unit
                    symbol = symbol.replace('.U', '-UN')
                elif 'type' in entry and entry['type'] == 'WARRANT':
                    # handle warrant
                    symbol = symbol.replace('.WS.A', '-WT')
                    symbol = symbol.replace('.WS', '-WT')
            if entry['market'] == 'indices':
                # handle indices
                symbol = symbol.replace('I:', '^')
                entry['type'] = 'IX'
            if len(symbol) > 2 and symbol[-2] == '.':
                if symbol[-1] <= 'C':
                    # handle class ticker
                    symbol = symbol.replace('.', '-')
                else:
                    # handle other
                    symbol = symbol.replace('.', '')

            write_data.append(entry)
            write_symbols.append(symbol)
        
        write_data = pd.DataFrame(write_data, index=write_symbols)
        write_data = write_data.reset_index().drop_duplicates(subset='index', keep='last').set_index('index')
        write_data.index.name = 'symbol'
        self.db.table_write('tickers', write_data)

        # update on every page to not loose data
        self.db.commit()

    def push_types_data(self, response_data):
        write_data =  []
        write_symbols = []
        for entry in response_data:
            symbol = entry.pop('code')
            write_data.append(entry)
            write_symbols.append(symbol)
        
        write_data = pd.DataFrame(write_data, index=write_symbols)
        write_data.index.name = 'code'
        self.db.table_write('types', write_data)

        # update on every page to not loose data
        self.db.commit()        

    def scrape_status(self, key_values=[], tabs=0):
        # get timestamps
        ftime = FTime()
        now = ftime.now_local

        status_db = self.db.table_read('status_db')
        tabs_string = '  '*tabs
        info = '%sdatabase: %s\n' % (tabs_string, self.db_name)
        status = None
        if status_db.shape[0] > 0:
            last_ts = status_db.loc['tickers', 'timestamp']
            last_time = ftime.get_from_ts_local(last_ts)
            next_time = ftime.get_offset(last_time, months=6)
            status = now >= next_time
            info += '%s  table: tickers\n' % (tabs_string)
            info += '%s    update     : %s\n' % (tabs_string, status)
            info += '%s    last update: %s\n' % (tabs_string, last_time)
            info += '%s    next update: %s\n' % (tabs_string, next_time)
        else:
            status = True
            info += '%s  table: tickers:\n' % (tabs_string)
            info += '%s    update     : %s\n' % (tabs_string, True)
            info += '%s    update     : Not scraped before\n' % (tabs_string)
        return status, info

    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'tickers':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.db.table_read('tickers', keys=key_values, columns=column_names)
                data = data.rename(columns={x[0]: x[1] for x in columns})
                return (data, self.db.timestamp)
            else:
                data = self.db.table_read('tickers', keys=key_values)
                return (data, self.db.timestamp)

    def get_vault_status(self, key_values, tabs=0):
        status, info = self.scrape_status(tabs=tabs)
        return info
