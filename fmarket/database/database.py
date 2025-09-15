import sqlite3, os, json
import numpy as np
import pandas as pd

class Database():
    def __init__(self, name, new=False):
        self.name = name
        file_path = 'database/%s.db' % self.name
        if new and os.path.exists(file_path): os.remove(file_path)
        self.connection = sqlite3.connect(file_path)
        self.timestamp = os.path.getmtime(file_path)

    def __del__(self):
        self.connection.commit()
        self.connection.close()

    def close(self):
        self.connection.close()
        self.connection = None

    def commit(self):
        self.connection.commit()

    def table_read(self, table_name, keys=[], columns=[]):
        cursor = self.connection.cursor()

        # get table info
        self.commit()
        table_info = cursor.execute("PRAGMA table_info('%s')" % table_name).fetchall()
        if len(table_info) == 0:
            cursor.close()
            # nothing to retrieve
            return pd.DataFrame()
        all_columns = [x[1] for x in table_info]
        json_columns = [x[1] for x in table_info if x[2] == 'JSON']
        primary_key_columns = [x[1] for x in table_info if x[5] == 1]
        
        # handle column selection
        exec_string = 'SELECT *'
        if len(columns) > 0:
            if len(primary_key_columns) > 0 and not primary_key_columns[0] in columns:
                columns = [primary_key_columns[0]] + columns
            columns = [x for x in columns if x in all_columns]
            columns_string = ','.join(['[%s]'%x for x in columns])
            exec_string = 'SELECT %s' % columns_string
        exec_string += " FROM '%s'" % table_name
        
        # handle keys selection
        if len(keys) > 0 and len(primary_key_columns) > 0:
            if len(keys) <= 30000:
                exec_string += " WHERE [%s] IN (%s)" % (primary_key_columns[0], ','.join(['?']*len(keys)))
                execution = cursor.execute(exec_string, tuple(keys))
            else:
                execution = cursor.execute(exec_string)
        else:
            execution = cursor.execute(exec_string)

        # fetch data
        table_columns = [x[0] for x in execution.description]
        table_data = execution.fetchall()
        cursor.close()
        table_data = pd.DataFrame(table_data, columns=table_columns)

        # handle primary key
        if len(primary_key_columns) > 0:
            table_data.set_index(primary_key_columns[0], inplace=True)
            table_data = table_data.sort_index()
            if len(keys) > 30000:
                table_data = table_data[table_data.index.isin(keys)]

        # change json to data if needed
        for column in table_data.columns:
            if column not in json_columns: continue
            table_data[column] = table_data[column].apply(lambda x: json.loads(x) if pd.notna(x) else x)

        return table_data
