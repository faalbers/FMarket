from .yahoof import YahooF
from ....database import Database
import logging, time
from pprint import pp
from datetime import datetime
import pandas as pd
import numpy as np
from ....utils import FTime

class YahooF_Fundamental_Quarterly(YahooF):
    db_name = 'yahoof_fundamental'

    def __init__(self):
        super().__init__()
        self.db = Database(self.db_name)

    def scrape_data(self, key_values=[], forced=False):
        # check status
        symbols, info = self.scrape_status(key_values=key_values, forced=forced)
        if len(symbols) == 0: return

        self.logger = logging.getLogger('YahooF_Fundamental_Quarterly'.ljust(25, ' '))

        self.logger.info('start update')
        
        # backup first
        self.logger.info(self.db.backup())

        procs = {
            'income_stmt_quarterly': (self.proc_income_stmt_quarterly,),
            'cash_flow_quarterly': (self.proc_cash_flow_quarterly, ('income_stmt_quarterly', 'do_quarterly')),
            'balance_sheet_quarterly': (self.proc_balance_sheet_quarterly, ('income_stmt_quarterly', 'do_quarterly')),
            'income_stmt_ttm': (self.proc_income_stmt_ttm, ('income_stmt_quarterly', 'do_ttm')),
            'cash_flow_ttm': (self.proc_cash_flow_ttm, ('income_stmt_ttm', 'do_ttm')),
        }
        self.multi_exec(procs, symbols)

        self.logger.info('update done')
    
    def proc_income_stmt_quarterly(self, ticker, results):
        while True:
            try:
                income_stmt_quarterly = ticker.get_income_stmt(freq='quarterly')
                if not isinstance(income_stmt_quarterly, type(None)):
                    if not income_stmt_quarterly.empty:
                        valid_dates = income_stmt_quarterly.loc['TotalRevenue'].notna()
                        results['status']['do_ttm'] = not valid_dates.iloc[0]
                        income_stmt_quarterly = income_stmt_quarterly.loc[:, valid_dates]
                        if not income_stmt_quarterly.empty:
                            # valid data
                            results['data'] = income_stmt_quarterly
                            results['status']['do_quarterly'] = True
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

    def proc_cash_flow_quarterly(self, ticker, results):
        while True:
            try:
                cash_flow_quarterly = ticker.get_cash_flow(freq='quarterly')
                if not isinstance(cash_flow_quarterly, type(None)):
                    if cash_flow_quarterly.shape[0] > 0:
                        results['data'] = cash_flow_quarterly
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

    def proc_balance_sheet_quarterly(self, ticker, results):
        while True:
            try:
                balance_sheet_quarterly = ticker.get_balance_sheet(freq='quarterly')
                if not isinstance(balance_sheet_quarterly, type(None)):
                    if balance_sheet_quarterly.shape[0] > 0:
                        results['data'] = balance_sheet_quarterly
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

    def proc_income_stmt_ttm(self, ticker, results):
        while True:
            try:
                income_stmt_ttm = ticker.get_income_stmt(freq='trailing')
                if not isinstance(income_stmt_ttm, type(None)):
                    if income_stmt_ttm.shape[0] > 0:
                        results['data'] = income_stmt_ttm
                        results['status']['do_ttm'] = True
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

    def proc_cash_flow_ttm(self, ticker, results):
        while True:
            try:
                cash_flow_ttm = ticker.get_cash_flow(freq='trailing')
                if not isinstance(cash_flow_ttm, type(None)):
                    if cash_flow_ttm.shape[0] > 0:
                        results['data'] = cash_flow_ttm
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
            'quarterly': int(ftime.now_local.timestamp()),
            }
        status = pd.DataFrame(status_init, index=[symbol])
        status.index.name = 'symbol'

        ok = False
        quarterly = pd.DataFrame()
        ttm = pd.DataFrame()
        if 'income_stmt_quarterly' in response_data:
            ok = True
            quarterly = pd.concat([quarterly, response_data['income_stmt_quarterly']['data']])
        
        if 'cash_flow_quarterly' in response_data:
            concat_data = response_data['cash_flow_quarterly']['data']
            concat_data = concat_data.loc[:, concat_data.columns.isin(quarterly.columns)]
            quarterly = pd.concat([quarterly, concat_data])
        
        if 'balance_sheet_quarterly' in response_data:
            concat_data = response_data['balance_sheet_quarterly']['data']
            concat_data = concat_data.loc[:, concat_data.columns.isin(quarterly.columns)]
            quarterly = pd.concat([quarterly, concat_data])
        
        if 'income_stmt_ttm' in response_data:
            ttm = pd.concat([ttm, response_data['income_stmt_ttm']['data']])
        elif 'income_stmt_quarterly' in response_data:
            income_stmt_ttm = response_data['income_stmt_quarterly']['data'].T.head(4)
            columns_last = [c for c in ['TaxRateForCalcs', 'DilutedAverageShares', 'BasicAverageShares'] if c in income_stmt_ttm.columns]
            if len(columns_last) > 0:
                last_quarter = income_stmt_ttm[columns_last].mean()
            income_stmt_ttm_date = income_stmt_ttm.index[0]
            income_stmt_ttm = income_stmt_ttm.sum().replace(0, np.nan)
            if len(columns_last) > 0:
                income_stmt_ttm.loc[columns_last] = last_quarter
            income_stmt_ttm.name = income_stmt_ttm_date
            income_stmt_ttm = income_stmt_ttm.to_frame()
            ttm = pd.concat([ttm, income_stmt_ttm])
        
        if 'cash_flow_ttm' in response_data:
            ttm = pd.concat([ttm, response_data['cash_flow_ttm']['data']])
        elif 'cash_flow_quarterly' in response_data:
            cash_flow_ttm = response_data['cash_flow_quarterly']['data'].T.head(4)
            overwrite_params = {}
            if 'BeginningCashPosition' in cash_flow_ttm.columns:
                overwrite_params['BeginningCashPosition'] = cash_flow_ttm.iloc[-1]['BeginningCashPosition']
            if 'EndCashPosition' in cash_flow_ttm.columns:
                overwrite_params['EndCashPosition'] = cash_flow_ttm.iloc[0]['EndCashPosition']
            cash_flow_ttm_date = cash_flow_ttm.index[0]
            cash_flow_ttm = cash_flow_ttm.sum().replace(0, np.nan)
            for param in overwrite_params:
                cash_flow_ttm.loc[param] = overwrite_params[param]
            cash_flow_ttm.name = cash_flow_ttm_date
            cash_flow_ttm = cash_flow_ttm.to_frame()
            ttm = pd.concat([ttm, cash_flow_ttm])

        if quarterly.shape[0] > 0:
            quarterly = quarterly.T.infer_objects()
            quarterly.index = [int(ts.timestamp()) for ts in quarterly.index]
            quarterly.index.name = 'timestamp'
            quarterly.sort_index(inplace=True)
            quarterly = quarterly.copy() # to avoid 'DataFrame is highly fragmented'
            quarterly = quarterly.dropna(how='all', axis=0)
            status.loc[symbol, 'quarterly_last'] = quarterly.index[-1]
            status.loc[symbol, 'quarterly_count'] = quarterly.shape[0]
            self.db.table_write_reference(symbol, 'quarterly', quarterly, replace_table=True)

        if ttm.shape[0] > 0:
            ttm = ttm.T.infer_objects()
            ttm.index = [int(ts.timestamp()) for ts in ttm.index]
            ttm.index.name = 'timestamp'
            ttm.sort_index(inplace=True)
            ttm = ttm.copy() # to avoid 'DataFrame is highly fragmented'
            ttm = ttm.dropna(how='all', axis=0)
            if ttm.shape[0] > 1:
                ttm.iloc[-1] = ttm.sum()
                ttm = ttm.iloc[-1:]
            ttm.reset_index(inplace=True)
            ttm.index = [symbol]
            ttm.index.name = 'symbol'
            status.loc[symbol, 'ttm_last'] = ttm.loc[symbol, 'timestamp']
            self.db.table_write('ttm', ttm)

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
        info += '%s  reference table: quarterly:\n' % (tabs_string)
        status = []
        if forced:
            # we are forcing all symbols
            status = key_values
            info += '%s    update     : %s symbols (forced)\n' % (tabs_string, len(status))
        else:
            # do status check
            if status_db.shape[0] > 0 and 'quarterly' in status_db.columns:
                symbols_skip = status_db['quarterly'] >= five_days_ts # do not handle if done 5 days ago
                symbols_skip |= (status_db['quarterly_last'] + (3600*24*(31*3+14))) > now_utc_ts # do not get if last quarterly has not passed 1 quarters plus yet
                symbols_skip |= (status_db['quarterly'] - status_db['quarterly_last']) > (3600*24*356) # do not get if last quarterly was more then a year ago

                # symbols_skip |= status_db['quarterly'] > last_quarter_ts
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
        if data_name in ['quarterly']:
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
