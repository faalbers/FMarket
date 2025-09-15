from .fmp import FMP
from ....database import Database
from datetime import datetime
import logging

class FMP_Stocklist(FMP):
    db_name = 'fmp_stocklist'

    def __init__(self):
        self.db = Database(self.db_name)

    def scrape_data(self, key_values=[]):
        # create logger with at least 20 character logger name
        logger = logging.getLogger('FMP_Stocklist'.ljust(20, ' '))
        logger.info(self.db_name)

    def scrape_status(self, key_values=[], tabs=0):
        status_db = self.db.table_read('status_db')
        tabs_string = '  '*tabs
        info = '%sdatabase: %s\n' % (tabs_string, self.db_name)
        status = None
        if status_db.shape[0] > 0:
            timestamp_pdt = int(datetime.now().timestamp())
            timestamp_last = status_db.loc['stocklist', 'timestamp']
            timestamp_next = timestamp_last - (3600 * 24 * 182)
            status = timestamp_next > timestamp_last
            info += '%s  table: stocklist\n' % (tabs_string)
            info += '%s    update     : %s\n' % (tabs_string, status)
            info += '%s    last update: %s\n' % (tabs_string, datetime.fromtimestamp(timestamp_last))
            info += '%s    next update: %s\n' % (tabs_string, datetime.fromtimestamp(timestamp_next))
        else:
            status = True
            info += '%s  table: stocklist:\n' % (tabs_string)
            info += '%s    update     : %s\n' % (tabs_string, True)
            info += '%s    update     : Not scraped before\n' % (tabs_string)
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
