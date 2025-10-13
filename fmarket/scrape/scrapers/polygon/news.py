from .polygon import Polygon
import logging
from ....database import Database
from ....utils import FTime
from pprint import pp
import pandas as pd
import re

class Polygon_News(Polygon):
    db_name = 'polygon_news'

    def __init__(self):
        super().__init__()
        self.db = Database(self.db_name)

    def scrape_data(self, key_values=[], forced=False):
        # check status
        status, info = self.scrape_status(key_values=key_values, forced=forced)
        # if isinstance(status, str):

        self.logger = logging.getLogger('Polygon_News'.ljust(25, ' '))

        self.logger.info('start update')
        
        # backup first
        self.logger.info(self.db.backup())

        # get news
        request_arguments = {
            'url': 'https://api.polygon.io/v2/reference/news',
            'params': {
                'limit': 1000,
                'sort': 'published_utc',
                'order': 'asc'
            },
        }

        # check if we need to do them all or just from status
        if isinstance(status, str):
            self.last_published_utc = status
            request_arguments['params']['published_utc.gt'] = status
        else:
            self.last_published_utc = None

        self.request(request_arguments, self.push_news_data)

        # update status
        status_db = pd.DataFrame([{'last_published_utc': self.last_published_utc}], index=['news'])
        status_db.index.name = 'table_name'
        self.db.table_write('status_db', status_db, replace=True)

        self.logger.info('update done')

    def push_news_data(self, response_data):
        # do nothing of response is empty
        if len(response_data) > 0:
            news_block = pd.DataFrame(response_data)
            news_block.set_index('id', inplace=True)
            self.last_published_utc = str(news_block.iloc[-1]['published_utc'])

            # write news
            self.db.table_write('news', news_block)

            # create index references
            symbol_ids = {}
            for id, news_data in news_block.iterrows():
                for ticker in news_data['tickers']:
                    if not ticker.isupper():
                        # fix ticker names with non all upper case
                        lower_cases = re.findall('[a-z]', ticker)
                        if len(lower_cases) > 0:
                            if lower_cases[0] == 'p':
                                ticker = ticker.replace('p', '-P')
                            else:
                                ticker = ticker.replace(lower_cases[0], '-' + lower_cases[0].upper() + 'I')
                        else:
                            continue
                    if not ticker in symbol_ids:
                        symbol_ids[ticker] = []
                    symbol_ids[ticker].append(id)
            for symbol, ids in symbol_ids.items():
                df = pd.DataFrame(ids, columns=['ids'])
                self.db.table_write_reference(symbol, 'ids', df)
            
            # update on every page to not loose data
            self.db.commit()

    def scrape_status(self, key_values=[], forced=False, tabs=0):
        # get timestamps
        ftime = FTime()
        now = ftime.now_local

        status_db = self.db.table_read('status_db')
        tabs_string = '  '*tabs
        info = '%sdatabase: %s\n' % (tabs_string, self.db_name)
        info += '%s  table: news\n' % (tabs_string)
        status = None
        if status_db.shape[0] > 0:
            updated_at = status_db.loc['news', 'last_published_utc']
            update_from = ftime.get_date_utc(updated_at, format='%Y-%m-%dT%H:%M:%SZ')
            update_from = ftime.get_offset(update_from, minutes=1).strftime('%Y-%m-%dT%H:%M:%SZ')
            status = update_from
            info += '%s    last update: %s\n' % (tabs_string, updated_at)
        else:
            info += '%s    update     : Not scraped before\n' % (tabs_string)
        
        if isinstance(status, str):
            info += '%s    update     : %s\n' % (tabs_string, status)
        else:
            info += '%s    update     : all\n' % (tabs_string)
        
        return status, info

    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'news_polygon':
            data = {}
            ids_reference = self.db.table_read_reference('ids', keys=key_values)
            for symbol, ids in ids_reference.items():
                if len(columns) > 0:
                    column_names = ['published_utc']+[x[0] for x in columns]
                    df = self.db.table_read('news', keys=ids['ids'].tolist(), columns=column_names)
                    columns_rename = {x[0]: x[1] for x in columns if (x[0] in df.columns) and (x[1] != None)}
                    if len(columns_rename) > 0:
                        df = df.rename(columns=columns_rename)
                else:
                    df = self.db.table_read('news', keys=ids['ids'].tolist())
                df['date'] = pd.to_datetime(df['published_utc'], format='%Y-%m-%dT%H:%M:%SZ')
                df = df.drop('published_utc', axis=1)
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)
                data[symbol] = df

            return (data, self.db.timestamp)

            # if len(columns) > 0:
            #     column_names = [x[0] for x in columns]
            #     data = self.db.timeseries_read('news', keys=key_values, columns=column_names)
            #     for symbol in data:
            #         data[symbol] = data[symbol].rename(columns={x[0]: x[1] for x in columns})
            #     return (data, self.db.timestamp)
            # else:
            #     # data = self.get_news(symbols=key_values)
            #     data = self.db.timeseries_read('news', keys=key_values)
            #     return (data, self.db.timestamp)

    def get_vault_params(self, data_name):
        if data_name == 'news_polygon':
            references = sorted(self.db.table_read_df('table_reference')['news'])
            max_len = 0
            for reference in references:
                column_types = self.db.get_table_info(reference)['columnTypes']
                column_types.pop('timestamp')
                # if len(column_types) > max_len:
                #     max_len = len(column_types)
                #     print(max_len)
                return(column_types)
