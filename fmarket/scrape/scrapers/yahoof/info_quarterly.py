from .yahoof import YahooF
from ....database import Database
import logging, time
from pprint import pp
from datetime import datetime
import pandas as pd
from ....utils import FTime

class YahooF_Info_Quarterly(YahooF):
    db_name = 'yahoof_info'

    def __init__(self):
        super().__init__()
        self.db = Database(self.db_name)

    def scrape_data(self, key_values=[], forced=False):
        # check status
        symbols, info = self.scrape_status(key_values=key_values, forced=forced)
        if len(symbols) == 0: return

        self.logger = logging.getLogger('YahooF_Info_Quarterly'.ljust(25, ' '))

        self.logger.info('start update')
        
        # backup first
        self.logger.info(self.db.backup())

        procs = {
            'earnings_estimate': self.proc_earnings_estimate,
            # 'revenue_estimate': self.proc_revenue_estimate,
            'growth_estimates': self.proc_growth_estimates,
        }
        self.multi_exec(procs, symbols)

        self.logger.info('update done')
    
    def proc_earnings_estimate(self,ticker):
        data = None
        while True:
            try:
                earnings_estimate = ticker.earnings_estimate
                if not isinstance(earnings_estimate, type(None)) and len(earnings_estimate) > 0:
                    data = earnings_estimate
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

    # def proc_revenue_estimate(self,ticker):
    #     data = None
    #     while True:
    #         try:
    #             revenue_estimate = ticker.revenue_estimate
    #             if not isinstance(revenue_estimate, type(None)) and len(revenue_estimate) > 0:
    #                 data = revenue_estimate
    #         except Exception as e:
    #             if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
    #                 self.logger.info('Rate Limeit: wait 60 seconds')
    #                 time.sleep(60)
    #                 continue
    #             else:
    #                 pass
    #                 # data[2]['info'] = str(e)
    #         break
    #     return data

    def proc_growth_estimates(self,ticker):
        data = None
        while True:
            try:
                growth_estimates = ticker.growth_estimates
                if not isinstance(growth_estimates, type(None)) and len(growth_estimates) > 0:
                    data = growth_estimates
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

        valid = False
        info = {}
        if not isinstance(response_data['earnings_estimate'], type(None)):
            info['earningsEstimate'] = response_data['earnings_estimate'].T.to_dict()
        # if not isinstance(response_data['revenue_estimate'], type(None)):
        #     info['revenueEstimate'] = response_data['revenue_estimate'].T.to_dict()
        if not isinstance(response_data['growth_estimates'], type(None)):
            info['growthEstimates'] = response_data['growth_estimates'].T.to_dict()

        status = pd.DataFrame({'info_quarterly': 0}, index=[symbol])
        status.index.name = 'symbol'

        if len(info) > 0: # we found stuff
            valid = True
            info = pd.DataFrame([info], index=[symbol])
            info.index.name = 'symbol'
            self.db.table_write('info', info)
            status.loc[symbol, 'info_quarterly'] = int(ftime.now_local.timestamp())
            valid = True
        
        # update status
        self.db.table_write('status_db', status)
        
        print(symbol, valid)
        return valid

    def scrape_status(self, key_values=[], forced=False, tabs=0):
        # timestamps
        ftime = FTime()
        five_days_ts = ftime.get_offset(ftime.now_local, days=-5).timestamp()

        status_db = self.db.table_read('status_db')
        tabs_string = '  '*tabs
        info = '%sdatabase: %s, forced: %s\n' % (tabs_string, self.db_name, forced)
        info += '%s  table: info (add quarterly data):\n' % (tabs_string)
        status = []
        if forced:
            # we are forcing all symbols
            status = key_values
            info += '%s    update     : %s symbols (forced)\n' % (tabs_string, len(status))
        else:
            # do status check
            if status_db.shape[0] > 0 and 'info_quarterly' in status_db.columns:
                symbols_skip = status_db['info_quarterly'] == 0 # skip symbols that did not work last time
                symbols_skip |= status_db['info_quarterly'] >= five_days_ts # skip symbols that were done within the last 5 days
                status = sorted(set(key_values).difference(status_db[symbols_skip].index))
            else:
                # we add all key_values to status
                status = key_values
                info += '%s    update     : Not scraped before\n' % (tabs_string)

            info += '%s    update     : %s symbols\n' % (tabs_string, len(status))
        
        return status, info

    def scrape_status_old(self, key_values=[], forced=False, tabs=0):
        # timestamps
        ftime = FTime()
        now_ts = ftime.now_local.timestamp()
        last_q_one_week_ts = ftime.get_quarter_begin(ftime.now_local)
        last_q_one_week_ts = ftime.get_offset(last_q_one_week_ts, weeks=1).timestamp()

        status_db = self.db.table_read('status_db')
        tabs_string = '  '*tabs
        info = '%sdatabase: %s, forced: %s\n' % (tabs_string, self.db_name, forced)
        info += '%s  table: info (add quarterly data):\n' % (tabs_string)
        status = []
        if forced:
            # we are forcing all symbols
            status = key_values
            info += '%s    update     : %s symbols (forced)\n' % (tabs_string, len(status))
        else:
            # do status check
            if status_db.shape[0] > 0 and 'info_quarterly' in status_db.columns:
                symbols_skip = status_db['info_quarterly'] == 0 # skip symbols that did not work last time
                symbols_skip |= (status_db['info_quarterly'] >= last_q_one_week_ts) | (now_ts <= last_q_one_week_ts) # skip if quarter done
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
