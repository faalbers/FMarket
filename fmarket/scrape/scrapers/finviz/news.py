from .finviz import Finviz
import logging
from ....database import Database
from ....utils import FTime, Stop
import pandas as pd

class Finviz_News(Finviz):
    db_name = 'finviz_news'

    def __init__(self):
        super().__init__()
        self.db = Database(self.db_name)

    def scrape_data(self, key_values=[], forced=False):
        # check status
        symbols, info = self.scrape_status(key_values=key_values, forced=forced)
        if len(symbols) == 0: return

        self.logger = logging.getLogger('Finviz_News'.ljust(25, ' '))

        self.logger.info('start update')
        
        # backup first
        self.logger.info(self.db.backup())

        stop = Stop()
        symbols_done = 0
        found = 0
        for symbol in symbols:
            if (symbols_done % 100) == 0:
                self.db.commit()
                self.logger.info('symbols still to do and found so far: (%s / %s)' % (len(symbols) - symbols_done, found))
            if self.request_news(symbol): found += 1
            symbols_done += 1
            if stop.is_set:
                self.logger.info('manually stopped request')
                self.logger.info('symbols done       : %s' % symbols_done)
                self.db.commit()
                break
        self.logger.info('total symbols found: %s' % (found))

        self.logger.info('update done')

    def push_api_data(self, symbol, response_data):
        ftime = FTime()
        symbol = symbol.upper()

        valid = not response_data.empty
        if valid:
            response_data.sort_values(by='Date', inplace=True)
            response_data.reset_index(drop=True, inplace=True)
            response_data['Date'] = response_data['Date'].apply(lambda x: int(x.timestamp()))
            if not response_data['Date'].is_unique:
                # add a second to not unique timestamps
                grouped_df = response_data.groupby('Date')
                for timestamp, group in grouped_df.groups.items():
                    if group.shape[0] > 1:
                        for index in group[1:]:
                            timestamp += 1
                            response_data.loc[index, 'Date'] = timestamp
            response_data.set_index('Date', verify_integrity=True, inplace=True)
            response_data.index.name = 'timestamp'
            self.db.table_write_reference(symbol, 'news', response_data, update=False)

        # update last time we checked on status
        status = {'news': int(ftime.now_local.timestamp())}
        status = pd.DataFrame([status], index=[symbol])
        status.index.name = 'symbol'
        self.db.table_write('status_db', status)

        return valid
 
    def scrape_status(self, key_values=[], forced=False, tabs=0):
        # timestamps
        ftime = FTime()
        five_days_ts = ftime.get_offset(ftime.now_local, days=-5).timestamp()

        status_db = self.db.table_read('status_db')
        tabs_string = '  '*tabs
        info = '%sdatabase: %s\n' % (tabs_string, self.db_name)
        info += '%s  table: news\n' % (tabs_string)
        status = []
        if forced:
            # we are forcing all symbols
            status = key_values
            info += '%s    update     : %s symbols (forced)\n' % (tabs_string, len(status))
        else:
            # do status check
            if status_db.shape[0] > 0 and 'news' in status_db.columns:
                symbols_skip = status_db['news'] >= five_days_ts # skip symbols that were done within the last 5 days
                status = sorted(set(key_values).difference(status_db[symbols_skip].index))
            else:
                status = key_values
                info += '%s    update     : Not scraped before\n' % (tabs_string)
            
            info += '%s    update     : %s symbols\n' % (tabs_string, len(status))
        
        return status, info

    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'news_finviz':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.db.timeseries_read('news', keys=key_values, columns=column_names)
                for symbol in data:
                    data[symbol] = data[symbol].rename(columns={x[0]: x[1] for x in columns})
                # return (data, self.db.timestamp)
                return data
            else:
                data = self.db.timeseries_read('news', keys=key_values)
                # return (data, self.db.timestamp)
                return data
