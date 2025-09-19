from .yahoof import YahooF
from ....database import Database
import logging, time
from pprint import pp
from datetime import datetime
import pandas as pd
from ....utils import FTime

class YahooF_Chart(YahooF):
    db_name = 'yahoof_chart'

    def __init__(self):
        super().__init__()
        self.db = Database(self.db_name)

    def scrape_data(self, key_values=[]):
        # check status
        symbols, info = self.scrape_status(key_values=key_values)
        if len(symbols) == 0: return

        self.logger = logging.getLogger('YahooF_Chart'.ljust(20, ' '))

        self.logger.info('start update')
        
        # backup first
        self.logger.info(self.db.backup())

        procs = {
            'chart': self.proc_chart,
        }
        self.multi_exec(procs, symbols)

        self.logger.info('update done')
    
    def proc_chart(self,ticker):
        data = None
        while True:
            try:
                chart = ticker.history(period="10y",auto_adjust=False)
                if not isinstance(chart, type(None)) and chart.shape[0] > 0:
                    data = chart
            except Exception as e:
                if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                    self.logger.info('Rate Limeit: wait 60 seconds')
                    time.sleep(60)
                    continue
                else:
                    # TODO: implement error handling
                    pass
                    # data[2]['info'] = str(e)
            break
        return data

    def push_api_data(self, symbol, response_data):
        ftime = FTime()
        result_data = response_data['chart']

        status = pd.DataFrame({'chart': 0, 'chart_last': 0, 'chart_count': 0}, index=[symbol])
        status.index.name = 'symbol'

        valid = False
        if not isinstance(result_data, type(None)):
            # drop columns with mixed data types
            result_data = result_data.infer_objects()
            result_data.drop(result_data.dtypes[result_data.dtypes == object].index.tolist(), axis=1, inplace=True)

            # get data
            result_data.index = result_data.index.tz_convert('UTC').normalize()
            result_data.index = [int(ts.timestamp()) for ts in result_data.index]
            status.loc[symbol, 'chart'] = int(ftime.now_local.timestamp())
            status.loc[symbol, 'chart_last'] = result_data.index[-1]
            status.loc[symbol, 'chart_count'] = result_data.shape[0]
            result_data.index.name = 'timestamp'
            self.db.table_write_reference(symbol, 'chart', result_data, replace=True)
            valid = True

        # update status
        self.db.table_write('status_db', status)

        print(symbol, valid)
        return valid

    def scrape_status(self, key_values=[], tabs=0):
        # timestamps
        ftime = FTime()
        five_days_ts = ftime.get_offset(ftime.now_local, days=-5).timestamp()

        tabs_string = '  '*tabs
        info = '%sdatabase: %s\n' % (tabs_string, self.db_name)
        info += '%s  reference table: chart:\n' % (tabs_string)
        status = []
        status_db = self.db.table_read('status_db')
        if status_db.shape[0] > 0:
            symbols_skip = status_db['chart'] == 0 # skip symbols that did not work last time
            symbols_skip |= status_db['chart'] >= five_days_ts # skip symbols that were done within the last 5 days
            symbols_skip |= ((status_db['chart'] - status_db['chart_last']) / (3600*24)) > 7 # more the 7 days between last data and update
            status = sorted(set(key_values).difference(status_db[symbols_skip].index))
        else:
            # we add all key_values to status
            status = key_values
            info += '%s    update     : Not scraped before\n' % (tabs_string)
        
        # check market day and time
        if ftime.is_market_open:
            # don't update if market is open
            status = []
            info += '%s    update     : No chart scraping during market hours\n' % (tabs_string)
        
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
