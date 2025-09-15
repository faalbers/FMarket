from .yahoof import YahooF
from ....database import Database
import logging

class YahooF_Info(YahooF):
    db_name = 'yahoof_info'

    def __init__(self):
        self.db = Database(self.db_name)

    def scrape_data(self, key_values=[]):
        logger = logging.getLogger('YahooF_Info'.ljust(20, ' '))
        logger.info(self.db_name)

    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'info':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.db.table_read('info', keys=key_values, columns=column_names)
                data = data.rename(columns={x[0]: x[1] for x in columns})
                return (data, self.db.timestamp)
            else:
                data = self.db.table_read('info', keys=key_values)
                return (data, self.db.timestamp)

    def get_vault_status(self, key_values, tabs=0):
        return self.db_name+'\n'
