from ratelimit import limits, sleep_and_retry
import yfinance as yf
from .yahoof import YahooF
from ....database import Database
import logging, time
from pprint import pp
from datetime import datetime
import pandas as pd
from ....utils import FTime

class YahooF_SP500(YahooF):
    db_name = 'yahoof_info'

    def __init__(self):
        super().__init__()
        self.db = Database(self.db_name)

    @sleep_and_retry
    @limits(calls=1, period=2)
    def yf_search(self, text):
        search = yf.Search(text, max_results=100)
        found = []
        for quote in search.quotes:
            found.append(quote['symbol'])
        return found

    def scrape_data(self, key_values=[], forced=False):
        # check status
        symbols, info = self.scrape_status(key_values=key_values, forced=forced)
        if len(symbols) == 0: return

        self.logger = logging.getLogger('YahooF_SP500'.ljust(25, ' '))

        self.logger.info('start update')

        # find sp 500 symbols
        self.logger.info('searching for sp500 index symbols')
        # string_len = 9
        # symbols = ['^SP500-%s' % x for x in range(10, 61, 5)]
        # sp500_found = set()
        # while len(symbols) > 0:
        #     for symbol in symbols:
        #         sp500_found.update(self.yf_search(symbol))
        #     self.logger.info('found sp500 index symbols so far: %s' % len(sp500_found))
        #     string_len += 2
        #     symbols = sorted(set([s[:string_len] for s in sp500_found if len(s) >= string_len]))

        # symbols = sorted(sp500_found)
        # symbols = symbols + ['XLV', 'XLB', 'XLK', 'XLF', 'XLI', 'XLRE', 'XLC', 'XLU', 'XLE', 'XLP', 'XLY']
        symbols = ['XLV', 'XLB', 'XLK', 'XLF', 'XLI', 'XLRE', 'XLC', 'XLU', 'XLE', 'XLP', 'XLY']
        self.logger.info('found sp500 index symbols total : %s' % len(symbols))

        # backup first
        self.logger.info(self.db.backup())

        procs = {
            'info': (self.proc_info,),
        }
        self.multi_exec(procs, symbols)

        self.logger.info('update done')
    
    def proc_info(self, ticker, results):
        while True:
            try:
                info = ticker.info
                if not isinstance(info, type(None)) and 'quoteType' in info:
                    results['data'] = info
            except Exception as e:
                if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                    self.logger.info('Rate Limeit: wait 60 seconds')
                    time.sleep(60)
                    continue
                else:
                    pass
                    # data[2]['info'] = str(e)
            break

    def push_api_data(self, symbol, response_data, exec_count):
        ftime = FTime()
        result_data = response_data['info']

        status_init = {
            'info': int(ftime.now_local.timestamp()),
            'invalid': True,
        }
        status = pd.DataFrame(status_init, index=[symbol])
        status.index.name = 'symbol'

        ok = False
        if 'info' in response_data:
            ok = True
            info = response_data['info']['data']
            # clean up some stuff
            if 'companyOfficers' in info: info.pop('companyOfficers')
            if 'executiveTeam' in info: info.pop('executiveTeam')
            if 'symbol' in info: info.pop('symbol')
            info = pd.DataFrame([info], index=[symbol])
            info.index.name = 'symbol'
            status.loc[symbol, 'invalid'] = False
            self.db.table_write('info', info)

        # update status
        self.db.table_write('status_db', status)

        print(symbol, ok, exec_count)
        return ok

    def scrape_status(self, key_values=[], forced=False, tabs=0):
        # timestamps
        ftime = FTime()
        three_months_ts = ftime.get_offset(ftime.now_local, months=-5).timestamp()

        tabs_string = '  '*tabs
        info = '%sdatabase: %s\n' % (tabs_string, self.db_name)
        info += '%s  table: info:\n' % (tabs_string)
        status = []

        status_db = self.db.table_read('status_db')
        if status_db.empty:
            status = ['DO IT ALL']
            info += '%s    update     : Get all SP500 index symbols\n' % (tabs_string)
        else:
            sp500_status = status_db[status_db.index.str.startswith('^SP500')]
            if len(sp500_status) == 0:
                status = ['DO IT ALL']
                info += '%s    update     : Get all SP500 index symbols\n' % (tabs_string)
            elif (sp500_status['info'] < three_months_ts).any():
                status = ['DO IT ALL']
                info += '%s    update     : Get all SP500 index symbols\n' % (tabs_string)
            else:
                info += '%s    update     : SP500 index symbols do not need update\n' % (tabs_string)
        
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
