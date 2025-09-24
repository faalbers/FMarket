from .yahoof import YahooF
from ....database import Database
import logging, time
from pprint import pp
from datetime import datetime
import pandas as pd
from ....utils import FTime

class YahooF_Fundamental_Yearly(YahooF):
    db_name = 'yahoof_fundamental'

    def __init__(self):
        super().__init__()
        self.db = Database(self.db_name)

    def scrape_data(self, key_values=[]):
        # check status
        symbols, info = self.scrape_status(key_values=key_values)
        if len(symbols) == 0: return

        self.logger = logging.getLogger('YahooF_Fundamental_Yearly'.ljust(25, ' '))

        self.logger.info('start update')
        
        # backup first
        self.logger.info(self.db.backup())

        procs = {
            'income_stmt_yearly': self.proc_income_stmt_yearly,
            'cash_flow_yearly': self.proc_cash_flow_yearly,
            'balance_sheet_yearly': self.proc_balance_sheet_yearly,
        }
        self.multi_exec(procs, symbols)

        self.logger.info('update done')
    
    def proc_income_stmt_yearly(self,ticker):
        data = None
        while True:
            try:
                income_stmt_yearly = ticker.get_income_stmt(freq='yearly')
                if not isinstance(income_stmt_yearly, type(None)) and income_stmt_yearly.shape[0] > 0:
                    data = income_stmt_yearly
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

    def proc_cash_flow_yearly(self,ticker):
        data = None
        while True:
            try:
                cash_flow_yearly = ticker.get_cash_flow(freq='yearly')
                if not isinstance(cash_flow_yearly, type(None)) and cash_flow_yearly.shape[0] > 0:
                    data = cash_flow_yearly
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

    def proc_balance_sheet_yearly(self,ticker):
        data = None
        while True:
            try:
                balance_sheet_yearly = ticker.get_balance_sheet(freq='yearly')
                if not isinstance(balance_sheet_yearly, type(None)) and balance_sheet_yearly.shape[0] > 0:
                    data = balance_sheet_yearly
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

        status = pd.DataFrame({'yearly': 0, 'yearly_last': 0, 'yearly_count': 0}, index=[symbol])
        status.index.name = 'symbol'

        valid = False
        yearly = pd.DataFrame()
        if not isinstance(response_data['income_stmt_yearly'], type(None)):
            yearly = pd.concat([yearly, response_data['income_stmt_yearly']])
        if not isinstance(response_data['cash_flow_yearly'], type(None)):
            yearly = pd.concat([yearly, response_data['cash_flow_yearly']])
        if not isinstance(response_data['balance_sheet_yearly'], type(None)):
            yearly = pd.concat([yearly, response_data['balance_sheet_yearly']])
        
        if yearly.shape[0] > 0:
            valid = True
            yearly = yearly.T.infer_objects()
            yearly.index = [int(ts.timestamp()) for ts in yearly.index]
            yearly.index.name = 'timestamp'
            yearly.sort_index(inplace=True)
            yearly = yearly.copy() # to avoid 'DataFrame is highly fragmented'
            yearly = yearly.dropna(how='all', axis=0)
            status.loc[symbol, 'yearly'] = int(ftime.now_local.timestamp())
            status.loc[symbol, 'yearly_last'] = yearly.index[-1]
            status.loc[symbol, 'yearly_count'] = yearly.shape[0]
            self.db.table_write_reference(symbol, 'yearly', yearly, replace=True)

        # update status
        self.db.table_write('status_db', status)

        print(symbol, valid)
        return valid

    def scrape_status(self, key_values=[], tabs=0):
        # timestamps
        ftime = FTime()
        five_days_ts = ftime.get_offset(ftime.now_local, days=-5).timestamp()
        now_ts = ftime.now_local.timestamp()

        tabs_string = '  '*tabs
        info = '%sdatabase: %s\n' % (tabs_string, self.db_name)
        info += '%s  reference table: yearly:\n' % (tabs_string)
        status = []
        status_db = self.db.table_read('status_db')
        if status_db.shape[0] > 0 and 'yearly' in status_db.columns:
            symbols_skip = status_db['yearly'] == 0 # skip symbols that did not work last time
            symbols_skip |= status_db['yearly'] >= five_days_ts
            symbols_skip |= (status_db['yearly_last'] + (3600*24*(365+14))) > now_ts # skip the ones do not yet after a year
            status = sorted(set(key_values).difference(status_db[symbols_skip].index))
        else:
            # we add all key_values to status
            status = key_values
            info += '%s    update     : Not scraped before\n' % (tabs_string)
        
        info += '%s    update     : %s symbols\n' % (tabs_string, len(status))
        
        return status, info

    def get_vault_data(self, data_name, columns, key_values):
        if len(columns) > 0:
            column_names = [x[0] for x in columns]
            data = self.db.table_read(data_name, keys=key_values, columns=column_names)
            data = data.rename(columns={x[0]: x[1] for x in columns})
            return data
        else:
            data = self.db.table_read(data_name, keys=key_values)
            return data

    def get_vault_status(self, key_values, tabs=0):
        return self.db_name+'\n'
