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

    def scrape_data(self, key_values=[], forced=False):
        # check status
        symbols, info = self.scrape_status(key_values=key_values, forced=forced)
        if len(symbols) == 0: return

        self.logger = logging.getLogger('YahooF_Chart'.ljust(25, ' '))

        self.logger.info('start update')
        
        # backup first
        self.logger.info(self.db.backup())

        procs = {
            'chart': (self.proc_chart,),
        }
        self.multi_exec(procs, symbols)

        self.logger.info('update done')
    
    def proc_chart(self, ticker, results):
        while True:
            try:
                chart = ticker.history(period="10y",auto_adjust=False)
                if not isinstance(chart, type(None)) and not chart.empty:
                    results['data'] = chart
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

    def push_api_data(self, symbol, response_data, exec_count):
        ftime = FTime()

        status_init = {
            'chart': int(ftime.now_local.timestamp()),
        }
        status = pd.DataFrame(status_init, index=[symbol])
        status.index.name = 'symbol'

        ok = False
        if 'chart' in response_data:
            ok = True
            # drop columns with mixed data types
            result_data = response_data['chart']['data'].infer_objects()
            result_data.drop(result_data.dtypes[result_data.dtypes == object].index.tolist(), axis=1, inplace=True)

            # get data
            if result_data.shape[0] > 1:
                status.loc[symbol, 'chart_interval_days'] = result_data.index.diff().days.dropna().to_numpy().mean()
            result_data.index = result_data.index.tz_convert('UTC').normalize()
            result_data.index = [int(ts.timestamp()) for ts in result_data.index]
            status.loc[symbol, 'chart_last'] = result_data.index[-1]
            status.loc[symbol, 'chart_first'] = result_data.index[0]
            status.loc[symbol, 'chart_count'] = result_data.shape[0]
            active_years = ftime.get_from_ts_naive(result_data.index[-1]) - ftime.get_from_ts_naive(result_data.index[0])
            status.loc[symbol, 'chart_active_years'] = active_years.days / 365.0
            status.loc[symbol, 'chart_days_since'] = (status_init['chart'] - result_data.index[-1]) / (3600*24)
            result_data.index.name = 'timestamp'
            self.db.table_write_reference(symbol, 'chart', result_data, replace_table=True)

        # update status
        self.db.table_write('status_db', status)

        print(symbol, ok, exec_count)
        return ok

    def scrape_status(self, key_values=[], forced=False, tabs=0):
        # timestamps
        ftime = FTime()
        five_days_ts = ftime.get_offset(ftime.now_local, days=-5).timestamp()
        now_utc_ts = ftime.now_utc.timestamp()

        status_db = self.db.table_read('status_db')
        tabs_string = '  '*tabs
        info = '%sdatabase: %s\n' % (tabs_string, self.db_name)
        info += '%s  reference table: chart:\n' % (tabs_string)
        status = []
        if forced:
            # we are forcing all symbols
            status = key_values
            info += '%s    update     : %s symbols (forced)\n' % (tabs_string, len(status))
        else:
            # do status check
            if status_db.shape[0] > 0 and 'chart' in status_db.columns:
                symbols_skip = status_db['chart'] >= five_days_ts
                symbols_skip |= status_db['chart_last'].isna()
                symbols_skip |= (status_db['chart_count'] == 1) & (status_db['chart_days_since'] > 30) # seems discontinued
                symbols_skip |= (now_utc_ts - status_db['chart_last']) / (3600*24) <= status_db['chart_interval_days']
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
        # get columns rename
        column_rename = {x[0]: x[1] for x in columns}
        
        # handle timeseries
        if data_name in ['chart']:
            data = self.db.timeseries_read(data_name, keys=key_values, columns=list(column_rename))
            if len(columns) > 0:
                for symbol, chart in data.items():
                    chart.rename(columns={c: cr for c, cr in column_rename.items() if c in chart.columns}, inplace=True)
            return data
        
        # handle tables
        data = self.db.table_read(data_name, keys=key_values, columns=list(column_rename))
        if len(columns) > 0:
            data.rename(columns={c: cr for c, cr in column_rename.items() if c in data.columns}, inplace=True)
        return data

    def get_vault_status(self, key_values, tabs=0):
        return self.db_name+'\n'
