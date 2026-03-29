from .yahoof import YahooF
from ....database import Database
import logging, time
from pprint import pp
from datetime import datetime
import pandas as pd
import numpy as np
from ....utils import FTime

class YahooF_Fundamental_Yearly(YahooF):
    db_name = 'yahoof_fundamental'

    def __init__(self):
        super().__init__()
        self.db = Database(self.db_name)

    def scrape_data(self, key_values=[], forced=False):
        # check status
        symbols, info = self.scrape_status(key_values=key_values, forced=forced)
        if len(symbols) == 0: return

        self.logger = logging.getLogger('YahooF_Fundamental_Yearly'.ljust(25, ' '))

        self.logger.info('start update')
        
        # backup first
        self.logger.info(self.db.backup())

        procs = {
            'income_stmt_yearly': (self.proc_income_stmt_yearly,),
            'cash_flow_yearly': (self.proc_cash_flow_yearly, ('income_stmt_yearly', 'do_yearly')),
            'balance_sheet_yearly': (self.proc_balance_sheet_yearly, ('income_stmt_yearly', 'do_yearly')),
        }
        self.multi_exec(procs, symbols)

        self.logger.info('update done')
    
    def proc_income_stmt_yearly(self, ticker, results):
        while True:
            try:
                income_stmt_yearly = ticker.get_income_stmt(freq='yearly')
                if not isinstance(income_stmt_yearly, type(None)):
                    if not income_stmt_yearly.empty:
                        valid_dates = income_stmt_yearly.loc['TotalRevenue'].notna()
                        income_stmt_yearly = income_stmt_yearly.loc[:, valid_dates]
                        if not income_stmt_yearly.empty:
                            # valid data
                            results['data'] = income_stmt_yearly
                            results['status']['do_yearly'] = True
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

    def proc_cash_flow_yearly(self, ticker, results):
        while True:
            try:
                cash_flow_yearly = ticker.get_cash_flow(freq='yearly')
                if not isinstance(cash_flow_yearly, type(None)):
                    if cash_flow_yearly.shape[0] > 0:
                        results['data'] = cash_flow_yearly
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

    def proc_balance_sheet_yearly(self, ticker, results):
        while True:
            try:
                balance_sheet_yearly = ticker.get_balance_sheet(freq='yearly')
                if not isinstance(balance_sheet_yearly, type(None)):
                    if balance_sheet_yearly.shape[0] > 0:
                        results['data'] = balance_sheet_yearly
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
            'yearly': int(ftime.now_local.timestamp()),
            }
        status = pd.DataFrame(status_init, index=[symbol])
        status.index.name = 'symbol'

        ok = False

        yearly = pd.DataFrame()
        if 'income_stmt_yearly' in response_data:
            ok = True
            yearly = pd.concat([yearly, response_data['income_stmt_yearly']['data']])
        if 'cash_flow_yearly' in response_data:
            concat_data = response_data['cash_flow_yearly']['data']
            concat_data = concat_data.loc[:, concat_data.columns.isin(yearly.columns)]
            yearly = pd.concat([yearly, concat_data])
        if 'balance_sheet_yearly' in response_data:
            concat_data = response_data['balance_sheet_yearly']['data']
            concat_data = concat_data.loc[:, concat_data.columns.isin(yearly.columns)]
            yearly = pd.concat([yearly, concat_data])
        
        if yearly.shape[0] > 0:
            valid = True
            yearly = yearly.T.infer_objects()
            yearly.index = [int(ts.timestamp()) for ts in yearly.index]
            yearly.index.name = 'timestamp'
            yearly.sort_index(inplace=True)
            yearly = yearly.copy() # to avoid 'DataFrame is highly fragmented'
            yearly = yearly.dropna(how='all', axis=0)
            status.loc[symbol, 'yearly_last'] = yearly.index[-1]
            status.loc[symbol, 'yearly_count'] = yearly.shape[0]
            self.db.table_write_reference(symbol, 'yearly', yearly, replace_table=True)

        # update status
        self.db.table_write('status_db', status)

        print(symbol, ok, exec_count)
        return ok

    def scrape_status(self, key_values=[], forced=False, tabs=0):
        # timestamps
        ftime = FTime()
        now_utc_ts = ftime.now_utc.timestamp()
        # last_quarter_ts = ftime.get_quarter_begin(ftime.now_utc).timestamp()
        five_days_ts = ftime.get_offset(ftime.now_local, days=-5).timestamp()
        now_ts = ftime.now_local.timestamp()

        status_db = self.db.table_read('status_db')
        tabs_string = '  '*tabs
        info = '%sdatabase: %s, forced: %s\n' % (tabs_string, self.db_name, forced)
        info += '%s  reference table: yearly:\n' % (tabs_string)
        status = []
        if forced:
            # we are forcing all symbols
            status = key_values
            info += '%s    update     : %s symbols (forced)\n' % (tabs_string, len(status))
        else:
            # do status check
            if status_db.shape[0] > 0 and 'yearly' in status_db.columns:
                symbols_skip = status_db['yearly'] >= five_days_ts # do not handle if done 5 days ago
                symbols_skip |= (status_db['yearly_last'] + (3600*24*(365+14))) > now_utc_ts # do not get if last yearly has not passed a year plus yet
                symbols_skip |= (status_db['yearly'] - status_db['yearly_last']) > (3600*24*(356*2)) # do not get if last yearly was more then two years ago
                # symbols_skip |= status_db['yearly'] > last_quarter_ts
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
        
        # handle timeseries
        data = self.db.timeseries_read(data_name, keys=key_values, columns=list(column_rename))
        if len(columns) > 0:
            for symbol, chart in data.items():
                chart.rename(columns={c: cr for c, cr in column_rename.items() if c in chart.columns}, inplace=True)
        return data
        
    def get_vault_status(self, key_values, tabs=0):
        return self.db_name+'\n'
