from .etrade import Etrade
from ....database import Database
from ....utils import FTime, Stop
import logging
from pprint import pp
import pandas as pd

class Etrade_Quote(Etrade):
    db_name = 'etrade_quote'

    def __init__(self):
        super().__init__()
        self.db = Database(self.db_name)

    def scrape_data(self, key_values=[], forced=False):
        # check status
        symbols, info = self.scrape_status(key_values=key_values, forced=forced)
        if len(symbols) == 0: return

        self.logger = logging.getLogger('Etrade_Quote'.ljust(25, ' '))

        self.logger.info('start update')
        
        # backup first
        self.logger.info(self.db.backup())

        # initialize a rauth session
        self.init_session()
        
        try:
            self.run_session(symbols)
        except Exception as e:
            print('Exception on Etrade Scrape:')
            print(str(e))

        # revoke rauth session
        self.revoke_session()

        self.logger.info('update done')

    def run_session(self, symbols):
        stop = Stop()
        self.logger.info('symbols processing : %s' % len(symbols))

        # create symbol blocks
        block_size = 50
        block_end = 0
        symbol_blocks = []
        for block_idx in range(int(len(symbols)/block_size)):
            block_start = block_idx*block_size
            block_end = block_start+block_size
            symbol_blocks.append(symbols[block_start:block_end])
        if len(symbols) % block_size > 0:
            symbol_blocks.append(symbols[block_end:])

        # go through symbol blocks and retrieve data
        count_done = 0
        failed = 0
        failed_total = 0
        for symbol_block in symbol_blocks:
            if (count_done % (block_size*2)) == 0:
                self.logger.info('to do: %s , failed: %s' % (len(symbols)-count_done, failed))
                self.db.commit()
                failed = 0
            
            equities = {}
            failed = 0
            # get ALL
            # symbols_string = ','.join(symbol_block)
            symbols_string = ','.join([x.lstrip('^') for x in symbol_block])
            request_arguments = {
                'url': 'https://api.etrade.com/v1/market/quote/%s.json' % symbols_string,
                'params': {
                    'detailFlag': 'ALL',
                    'overrideSymbolCount': 'true',
                },
            }

            mutual_funds = set()
            try:
                response = self.session_get(request_arguments)
            except Exception as e:
                self.logger.info('ALL session get error: %s' % (str(e)))
                self.logger.info('stopping')
                self.logger.info('done: %s , failed: %s' % (count_done, failed_total))
                self.db.commit()
                return
            if response.headers.get('content-type').startswith('application/json'):
                response_data = response.json()
                if 'QuoteResponse' in response_data:
                    response_data = response_data['QuoteResponse']
                    if 'QuoteData' in response_data:
                        for quote_data in response_data['QuoteData']:
                            product = quote_data['Product']
                            # symbol = product['symbol']
                            symbol = self.match_symbol(product['symbol'], symbol_block)
                            security_type = product['securityType']
                            if 'securitySubType' in product:
                                security_type = product['securitySubType']
                            if security_type in ['MF', 'MMF']:
                                mutual_funds.add(symbol)
                            else:
                                equities[symbol] = quote_data['All']
                                equities[symbol]['securityType'] = security_type
                                equities[symbol]['dateTimeUTC'] = quote_data['dateTimeUTC']
            else:
                print(mutual_funds)
                print(symbols_string)
                pp(response.text)
                self.db.commit()
                raise ValueError('no json content type on ALL')
            
            if len(mutual_funds) > 0:
                # get MF_DETAIL
                # symbols_string = ','.join(mutual_funds)
                symbols_string = ','.join([x.lstrip('^') for x in mutual_funds])
                request_arguments = {
                    'url': 'https://api.etrade.com/v1/market/quote/%s.json' % symbols_string,
                    'params': {
                        'detailFlag': 'MF_DETAIL',
                        'overrideSymbolCount': 'true',
                    },
                }

                try:
                    response = self.session_get(request_arguments)
                except Exception as e:
                    self.logger.info('MF_DETAIL session get error: %s' % (str(e)))
                    self.logger.info('stopping')
                    self.logger.info('done: %s , failed: %s' % (count_done, failed_total))
                    self.db.commit()
                    return
                if response.headers.get('content-type').startswith('application/json'):
                    response_data = response.json()
                    if 'QuoteResponse' in response_data:
                        response_data = response_data['QuoteResponse']
                        if 'QuoteData' in response_data:
                            for quote_data in response_data['QuoteData']:
                                product = quote_data['Product']
                                # symbol = product['symbol']
                                symbol = self.match_symbol(product['symbol'], mutual_funds)
                                security_type = product['securityType']
                                equities[symbol] = quote_data['MutualFund']
                                equities[symbol]['securityType'] = security_type
                                equities[symbol]['dateTimeUTC'] = quote_data['dateTimeUTC']
                else:
                    print(mutual_funds)
                    print(symbols_string)
                    pp(response.text)
                    self.db.commit()
                    raise ValueError('no json content type on MF_DETAIL')

            # push into database
            for symbol in symbol_block:
                if not symbol in equities:
                    failed += 1
                    self.push_api_data(symbol, [False, None, 'no data'])
                else:
                    self.push_api_data(symbol, [True, equities[symbol], 'ok'])
            count_done += len(symbol_block)
            failed_total += failed
            self.db.commit()
            
            # manually stop if needed
            if stop.is_set:
                self.logger.info('manually stopped multi_exec')
                break

    def match_symbol(self, symbol, symbol_block):
        if symbol in symbol_block:
            return symbol
        symbol = '^' + symbol
        if symbol in symbol_block:
            return symbol
        return None

    def push_api_data(self, symbol, result):
        fttime = FTime()
        valid = result[0]
        message = result[2]
        result = result[1]

        local_ts = 0
        if valid:
            result = pd.DataFrame([result], index=[symbol])
            result.index.name = 'symbol'
            local_ts = int(fttime.now_local.timestamp())
            self.db.table_write('quote', result)

        status = pd.DataFrame([{'quote': local_ts}], index=[symbol])
        status.index.name = 'symbol'
        self.db.table_write('status_db', status)

        print(symbol, valid)

    def scrape_status(self, key_values=[], forced=False, tabs=0):
        # timestamps
        ftime = FTime()
        five_days_ts = ftime.get_offset(ftime.now_local, days=-5).timestamp()

        status_db = self.db.table_read('status_db')
        tabs_string = '  '*tabs
        info = '%sdatabase: %s\n' % (tabs_string, self.db_name)
        info += '%s  table: quote:\n' % (tabs_string)
        status = []
        if forced:
            # we are forcing all symbols
            status = key_values
            info += '%s    update     : %s symbols (forced)\n' % (tabs_string, len(status))
        else:
            # do status check
            if status_db.shape[0] > 0 and 'quote' in status_db.columns:
                symbols_skip = status_db['quote'] == 0 # skip symbols that did not work last time
                symbols_skip |= status_db['quote'] >= five_days_ts # skip symbols that were done within the last 5 days
                status = sorted(set(key_values).difference(status_db[symbols_skip].index))
            else:
                # we add all key_values to status
                status = key_values
                info += '%s    update     : Not scraped before\n' % (tabs_string)

            info += '%s    update     : %s symbols\n' % (tabs_string, len(status))
        
        return status, info
