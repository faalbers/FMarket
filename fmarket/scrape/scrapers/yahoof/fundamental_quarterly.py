from .yahoof import YahooF
from ....database import Database
import logging, time
from pprint import pp
from datetime import datetime
import pandas as pd
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
            'income_stmt_quarterly': self.proc_income_stmt_quarterly,
            'cash_flow_quarterly': self.proc_cash_flow_quarterly,
            'balance_sheet_quarterly': self.proc_balance_sheet_quarterly,
            'income_stmt_ttm': self.proc_income_stmt_ttm,
            'cash_flow_ttm': self.proc_cash_flow_ttm,
        }
        self.multi_exec(procs, symbols)

        self.logger.info('update done')
    
    def proc_income_stmt_quarterly(self,ticker):
        data = None
        while True:
            try:
                income_stmt_quarterly = ticker.get_income_stmt(freq='quarterly')
                if not isinstance(income_stmt_quarterly, type(None)) and income_stmt_quarterly.shape[0] > 0:
                    data = income_stmt_quarterly
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

    def proc_cash_flow_quarterly(self,ticker):
        data = None
        while True:
            try:
                cash_flow_quarterly = ticker.get_cash_flow(freq='quarterly')
                if not isinstance(cash_flow_quarterly, type(None)) and cash_flow_quarterly.shape[0] > 0:
                    data = cash_flow_quarterly
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

    def proc_balance_sheet_quarterly(self,ticker):
        data = None
        while True:
            try:
                balance_sheet_quarterly = ticker.get_balance_sheet(freq='quarterly')
                if not isinstance(balance_sheet_quarterly, type(None)) and balance_sheet_quarterly.shape[0] > 0:
                    data = balance_sheet_quarterly
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

    def proc_income_stmt_ttm(self,ticker):
        data = None
        while True:
            try:
                income_stmt_ttm = ticker.get_income_stmt(freq='trailing')
                if not isinstance(income_stmt_ttm, type(None)) and income_stmt_ttm.shape[0] > 0:
                    data = income_stmt_ttm
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

    def proc_cash_flow_ttm(self,ticker):
        data = None
        while True:
            try:
                cash_flow_ttm = ticker.get_cash_flow(freq='trailing')
                if not isinstance(cash_flow_ttm, type(None)) and cash_flow_ttm.shape[0] > 0:
                    data = cash_flow_ttm
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

        status = pd.DataFrame({'quarterly': 0, 'quarterly_last': 0, 'quarterly_count': 0}, index=[symbol])
        status.index.name = 'symbol'

        valid = False
        quarterly = pd.DataFrame()
        ttm = pd.DataFrame()
        if not isinstance(response_data['income_stmt_quarterly'], type(None)):
            quarterly = pd.concat([quarterly, response_data['income_stmt_quarterly']])
        if not isinstance(response_data['cash_flow_quarterly'], type(None)):
            quarterly = pd.concat([quarterly, response_data['cash_flow_quarterly']])
        if not isinstance(response_data['balance_sheet_quarterly'], type(None)):
            quarterly = pd.concat([quarterly, response_data['balance_sheet_quarterly']])
        if not isinstance(response_data['income_stmt_ttm'], type(None)):
            ttm = pd.concat([ttm, response_data['income_stmt_ttm']])
        if not isinstance(response_data['cash_flow_ttm'], type(None)):
            ttm = pd.concat([ttm, response_data['cash_flow_ttm']])
        
        
        if quarterly.shape[0] > 0:
            valid = True
            quarterly = quarterly.T.infer_objects()
            quarterly.index = [int(ts.timestamp()) for ts in quarterly.index]
            quarterly.index.name = 'timestamp'
            quarterly.sort_index(inplace=True)
            quarterly = quarterly.copy() # to avoid 'DataFrame is highly fragmented'
            quarterly = quarterly.dropna(how='all', axis=0)
            status.loc[symbol, 'quarterly'] = int(ftime.now_local.timestamp())
            status.loc[symbol, 'quarterly_last'] = quarterly.index[-1]
            status.loc[symbol, 'quarterly_count'] = quarterly.shape[0]
            self.db.table_write_reference(symbol, 'quarterly', quarterly, replace=True)

        if ttm.shape[0] > 0:
            valid = True
            ttm = ttm.T.infer_objects()
            ttm.index = [int(ts.timestamp()) for ts in ttm.index]
            ttm.index.name = 'timestamp'
            ttm.sort_index(inplace=True)
            ttm = ttm.copy() # to avoid 'DataFrame is highly fragmented'
            ttm = ttm.dropna(how='all', axis=0)
            if quarterly.shape[0] == 0:
                status.loc[symbol, 'quarterly'] = int(ftime.now_local.timestamp())
                status.loc[symbol, 'quarterly_last'] = ttm.index[-1]
                status.loc[symbol, 'quarterly_count'] = 0
            if ttm.shape[0] > 1:
                ttm.iloc[-1] = ttm.sum()
                ttm = ttm.iloc[-1:]
            ttm.reset_index(inplace=True)
            ttm.index = [symbol]
            ttm.index.name = 'symbol'
            self.db.table_write('ttm', ttm)

        # update status
        self.db.table_write('status_db', status)

        print(symbol, valid)
        return valid

    def scrape_status(self, key_values=[], forced=False, tabs=0):
        # timestamps
        ftime = FTime()
        five_days_ts = ftime.get_offset(ftime.now_local, days=-5).timestamp()
        now_ts = ftime.now_local.timestamp()

        status_db = self.db.table_read('status_db')
        tabs_string = '  '*tabs
        info = '%sdatabase: %s\n' % (tabs_string, self.db_name)
        info += '%s  reference table: quarterly:\n' % (tabs_string)
        status = []
        if forced:
            # we are forcing all symbols
            status = key_values
            info += '%s    update     : %s symbols (forced)\n' % (tabs_string, len(status))
        else:
            # do status check
            if status_db.shape[0] > 0 and 'quarterly' in status_db.columns:
                symbols_skip = status_db['quarterly'] == 0 # skip symbols that did not work last time
                symbols_skip |= status_db['quarterly'] >= five_days_ts
                symbols_skip |= (status_db['quarterly_last'] + (3600*24*(90+7))) > now_ts # skip the ones do not yet after a quarter
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
