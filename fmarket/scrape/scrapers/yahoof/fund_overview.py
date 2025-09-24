from .yahoof import YahooF
from ....database import Database
import logging, time
from pprint import pp
from datetime import datetime
import pandas as pd
from ....utils import FTime

class YahooF_Fund_Overview(YahooF):
    db_name = 'yahoof_info'

    def __init__(self):
        super().__init__()
        self.db = Database(self.db_name)

    def scrape_data(self, key_values=[]):
        # check status
        symbols, info = self.scrape_status(key_values=key_values)
        if len(symbols) == 0: return

        self.logger = logging.getLogger('YahooF_Fund_Overview'.ljust(25, ' '))

        self.logger.info('start update')
        
        # backup first
        self.logger.info(self.db.backup())

        procs = {
            'fund_overview': self.proc_fund_overview,
        }
        self.multi_exec(procs, symbols)

        self.logger.info('update done')
    
    def proc_fund_overview(self,ticker):
        data = None
        while True:
            try:
                fund_overview = ticker.funds_data.fund_overview
                if not isinstance(fund_overview, type(None)) and len(fund_overview) > 0:
                    data = fund_overview
            except Exception as e:
                if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                    self.logger.info('Rate Limeit: wait 60 seconds')
                    time.sleep(60)
                    continue
                else:
                    pass
            break
        return data

    def push_api_data(self, symbol, response_data):
        ftime = FTime()
        result_data = response_data['fund_overview']

        status = pd.DataFrame({'fund_overview': 0}, index=[symbol])
        status.index.name = 'symbol'

        valid = False
        if not isinstance(result_data, type(None)):
            result = pd.DataFrame([{'fundOverview': result_data}], index=[symbol])
            result.index.name = 'symbol'
            self.db.table_write('info', result)
            status.loc[symbol, 'fund_overview'] = int(ftime.now_local.timestamp())
            valid = True

        # update status
        self.db.table_write('status_db', status)

        return valid

    def scrape_status(self, key_values=[], tabs=0):
        # timestamps
        ftime = FTime()
        one_year_ts = ftime.get_offset(ftime.now_local, years=-1).timestamp()

        status_db = self.db.table_read('status_db')
        tabs_string = '  '*tabs
        info = '%sdatabase: %s\n' % (tabs_string, self.db_name)
        info += '%s  table: info (add fund_overview):\n' % (tabs_string)
        status = []
        if status_db.shape[0] > 0 and 'fund_overview' in status_db.columns:
            symbols_skip = status_db['fund_overview'] == 0 # skip symbols that did not work last time
            symbols_skip |= status_db['fund_overview'] >= one_year_ts # skip symbols that were done within the year
            status = sorted(set(key_values).difference(status_db[symbols_skip].index))
        else:
            # we add all key_values to status
            status = key_values
            info += '%s    update     : Not scraped before\n' % (tabs_string)

        info += '%s    update     : %s symbols\n' % (tabs_string, len(status))

        return status, info

    def get_vault_data(self, data_name, columns, key_values):
        # get columns rename
        column_rename = {x[0]: x[1] for x in columns}
        
        # handle tables
        data = self.db.table_read(data_name, keys=key_values, columns=list(column_rename))
        if len(columns) > 0:
            data.rename(columns={c: cr for c, cr in column_rename.items() if c in data.columns}, inplace=True)
        return data

    def get_vault_status(self, key_values, tabs=0):
        return self.db_name+'\n'
