from .yahoof import YahooF
from ....database import Database
import logging, time
from pprint import pp
from datetime import datetime
import pandas as pd
from ....utils import FTime

class YahooF_Info(YahooF):
    db_name = 'yahoof_info'

    def __init__(self):
        super().__init__()
        self.db = Database(self.db_name)

    def scrape_data(self, key_values=[]):
        # check status
        symbols, info = self.scrape_status(key_values=key_values)
        if len(symbols) == 0: return

        self.logger = logging.getLogger('YahooF_Info'.ljust(25, ' '))

        self.logger.info('start update')
        
        # backup first
        self.logger.info(self.db.backup())

        procs = {
            'info': self.proc_info,
        }
        self.multi_exec(procs, symbols)

        self.logger.info('update done')
    
    def proc_info(self,ticker):
        data = None
        while True:
            try:
                info = ticker.info
                if not isinstance(info, type(None)) and 'quoteType' in info:
                    data = info
                # else:
                #     data = 'info is None'
            except Exception as e:
                if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                    self.logger.info('Rate Limeit: wait 60 seconds')
                    time.sleep(60)
                    continue
                else:
                    pass
                    # data[2]['info'] = str(e)
            break
        return data

    def push_api_data(self, symbol, response_data):
        ftime = FTime()
        result_data = response_data['info']

        status = pd.DataFrame({'info': 0}, index=[symbol])
        status.index.name = 'symbol'

        valid = False
        if not isinstance(result_data, type(None)):
            # clean up some stuff
            if 'companyOfficers' in result_data: result_data.pop('companyOfficers')
            if 'executiveTeam' in result_data: result_data.pop('executiveTeam')
            if 'symbol' in result_data: result_data.pop('symbol')
            result = pd.DataFrame([result_data], index=[symbol])
            result.index.name = 'symbol'
            self.db.table_write('info', result)
            status.loc[symbol, 'info'] = int(ftime.now_local.timestamp())
            valid = True

        # update status
        self.db.table_write('status_db', status)

        print(symbol, valid)
        return valid

    def scrape_status(self, key_values=[], tabs=0):
        # timestamps
        ftime = FTime()
        five_days_ts = ftime.get_offset(ftime.now_local, days=-5).timestamp()

        status_db = self.db.table_read('status_db')
        tabs_string = '  '*tabs
        info = '%sdatabase: %s\n' % (tabs_string, self.db_name)
        info += '%s  table: info:\n' % (tabs_string)
        status = []
        if status_db.shape[0] > 0 and 'info' in status_db.columns:
            symbols_skip = status_db['info'] == 0 # skip symbols that did not work last time
            symbols_skip |= status_db['info'] >= five_days_ts # skip symbols that were done within the last 5 days
            status = sorted(set(key_values).difference(status_db[symbols_skip].index))
        else:
            # we add all key_values to status
            status = key_values
            info += '%s    update     : Not scraped before\n' % (tabs_string)

        info += '%s    update     : %s symbols\n' % (tabs_string, len(status))
        
        return status, info

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
