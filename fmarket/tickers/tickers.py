from ..vault import Vault
import pandas as pd

class Tickers():
    def __init__(self, symbols=[]):
        self.vault = Vault()
        self.__make_symbols(symbols)
        self.empty = self.__symbols.empty

    def __make_symbols(self, symbols):
        symbols_data_vault = self.vault.get_data('tickers', key_values=symbols)

        # start creating symbols
        self.__symbols = pd.DataFrame()

        # add stocklist
        if not symbols_data_vault['stocklist'].empty:
            self.__symbols = symbols_data_vault['stocklist']
            self.__symbols.rename(columns={'type': 'sub_type'}, inplace=True)
            self.__symbols['sub_type'] = self.__symbols['sub_type'].str.upper()
            self.__symbols.loc[self.__symbols['sub_type'] == 'STOCK', 'sub_type'] = 'CS'
            self.__symbols.loc[self.__symbols['sub_type'] == 'TRUST', 'sub_type'] = 'UNIT'

        # add tickers
        if not symbols_data_vault['tickers'].empty:
            self.__symbols = self.__symbols.merge(symbols_data_vault['tickers'],
                how='outer', left_index=True, right_index=True, suffixes=('_stocklist', '_tickers'))
            
            # consolidate sub_type
            if 'sub_type_tickers' in self.__symbols.columns:
                self.__symbols['sub_type'] = self.__symbols['sub_type_tickers']
                sub_type_nan = self.__symbols['sub_type'].isna()
                self.__symbols.loc[sub_type_nan,'sub_type'] = self.__symbols.loc[sub_type_nan,'sub_type_stocklist']
                self.__symbols.drop(['sub_type_stocklist', 'sub_type_tickers'], axis=1, inplace=True)
            self.__symbols.loc[self.__symbols['sub_type'].isna(),'sub_type'] = 'CS'

            # fill in missing names and drop name_tickers
            if 'name_tickers' in self.__symbols.columns:
                self.__symbols['name_stocklist'] = self.__symbols['name_stocklist'].fillna(self.__symbols['name_tickers'])
                self.__symbols.drop('name_tickers', axis=1, inplace=True)
                self.__symbols.rename(columns={'name_stocklist': 'name'}, inplace=True)

        # add info
        if not symbols_data_vault['info'].empty:
            self.__symbols = self.__symbols.merge(symbols_data_vault['info'],
                how='outer', left_index=True, right_index=True)
            
            # make all the tickers starting with ^ into index
            self.__symbols.loc[self.__symbols.index.str.startswith('^'), 'type'] = 'INDEX'

            # set name to name_short that are valid
            has_info_name = self.__symbols['name_short'].notna() & \
                ~pd.to_numeric(self.__symbols['name_short'], errors='coerce').notna()
            self.__symbols.loc[has_info_name, 'name'] = self.__symbols.loc[has_info_name, 'name_short']
            self.__symbols.drop(['name_short'], axis=1, inplace=True)

            # fill in missing types and sub_types with NONE
            self.__symbols.loc[self.__symbols['type'].isna(), 'type'] = 'NONE'
            self.__symbols.loc[self.__symbols['sub_type'].isna(), 'sub_type'] = 'NONE'

            # tag if in yahoof
            self.__symbols.loc[self.__symbols.index.isin(symbols_data_vault['info'].index),'yahoof'] = True

        # add chart activity
        if not symbols_data_vault['status_db_chart'].empty:
            self.__symbols = self.__symbols.merge(symbols_data_vault['status_db_chart'],
                how='outer', left_index=True, right_index=True)
            self.__symbols['days'] = ((self.__symbols['chart'] - self.__symbols['chart_last']) / (3600*24))
            self.__symbols['active'] = self.__symbols['days'] <= 7
            self.__symbols.drop(['chart', 'chart_last', 'days'], axis=1, inplace=True)

        # final cleanup
        self.__symbols.sort_index(inplace=True)

        # reorder columns
        columns = [c for c in ['name', 'type', 'sub_type', 'yahoof', 'active'] if c in self.__symbols.columns]
        self.__symbols = self.__symbols[columns]

    def get(self, yahoof=False, active=False):
        tickers = self.__symbols.copy()
        if active and 'active' in tickers.columns:
            tickers = tickers[tickers['active'] == True]
            tickers.drop('active', axis=1, inplace=True)
            tickers.drop('yahoof', axis=1, inplace=True)
        if yahoof and 'yahoof' in tickers.columns:
            tickers = tickers[tickers['yahoof'] == True]
            tickers.drop('yahoof', axis=1, inplace=True)

        return tickers

