from ratelimit import limits, sleep_and_retry
from ....utils import Stop
import yfinance as yf
import logging

class YahooF():
    @sleep_and_retry
    @limits(calls=100, period=60) # 6000/hour
    def exec_proc(self, proc, arguments):
        return proc(**arguments)

    def yfinancetest(self):
        ticker = yf.Ticker('AAPL')
        try:
            quoteType = ticker.fast_info['quoteType']
            if len(quoteType) == 0: return False
        except Exception as e:
            if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                print('Too Many Requests. Rate limited. Change VPN location')
                return False
        return True
    
    def __init__(self):
        # make yfinance non verbose
        yflogger = logging.getLogger('yfinance')
        yflogger.disabled = True
        yflogger.propagate = False

    def multi_exec(self, procs, symbols):
        stop = Stop()
        count_done = 0
        failed = 0
        failed_total = 0
        for symbol in symbols:
            if (count_done % 100) == 0:
                self.logger.info('to do: %s , failed: %s' % (len(symbols)-count_done, failed))
                self.db.commit()
                failed = 0
            
            ticker = yf.Ticker(symbol)
            data = {}
            exec_count = 0
            for data_name, proc_tuple in procs.items():
                proc = proc_tuple[0]
                # check status
                if len(proc_tuple) > 1:
                    data_name_check, check_name = proc_tuple[1]
                    if not data_name_check in data: continue
                    if not check_name in data[data_name_check]['status']: continue
                    if not data[data_name_check]['status'][check_name]: continue
                results = {
                    'data': None,
                    'status': {},
                }
                arguments = {'ticker': ticker, 'results': results}
                self.exec_proc(proc, arguments)
                exec_count += 1
                if isinstance(results['data'], type(None)): continue
                data[data_name] = results

            if not self.push_api_data(symbol, data, exec_count):
                failed += 1
                failed_total += 1
            
            count_done += 1
            
            # manually stop if needed
            if stop.is_set:
                self.logger.info('manually stopped multi_exec')
                self.db.commit()
                break
            
            # run a yfinance test every 100 entriesexec entries
            if (count_done % 100) == 0:
                if not self.exec_proc(self.yfinancetest, {}):
                    self.logger.info('yfinance not ok ...')
                    break
                else:
                    self.logger.info('yfinance still ok ...')
        
        self.logger.info('done: %s , failed: %s' % (count_done, failed_total))
    