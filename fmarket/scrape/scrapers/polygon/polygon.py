import requests
from data.keys import KEYS
from ratelimit import limits, sleep_and_retry
from pprint import pp
from ....utils import Stop

class Polygon():
    def __init__(self):
        self.init_session()

    def init_session(self):
        # create session
        params = {'apikey': KEYS['POLYGON']['KEY']}
        self.session = requests.Session()
        self.session.params.update(params)

    @sleep_and_retry
    @limits(calls=5, period=70)
    def session_get(self, request_arguments):
        return self.session.get(**request_arguments)
    
    # handle requests till they are exhausted
    def request(self, request_arguments, push_proc):
        stop = Stop()
        next_request_arguments = request_arguments
        entries = 0
        # runs = 10
        while next_request_arguments:
            response = self.session_get(next_request_arguments)
            if response.headers.get('content-type').startswith('application/json'):
                write_data = {}
                response_data = response.json()
                if 'results' in response_data:
                    push_proc(response_data['results'])
                else:
                    self.logger.info('no result in response chunk, stopping requests')
                    break
                if 'count' in response_data:
                    entries += response_data['count']
                self.logger.info('entries found: %s' % entries)
                next_request_arguments = None
                if 'next_url' in response_data:
                    next_request_arguments = {'url': response_data['next_url']}
            else:
                next_request_arguments = None
            
            if stop.is_set:
                self.logger.info('manually stopped request')
                self.logger.info('entries found: %s' % entries)
                self.db.commit()
                next_request_arguments = None
    