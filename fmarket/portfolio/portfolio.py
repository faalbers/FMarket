from ..globals import *
from .etrade import Etrade
from .fidelity import Fidelity
from .broker import Broker
from ..database import Database
from ..tickers import Tickers
from ..utils import FTime, storage
from ..report import Report
from ..vault.catalog import Catalog
from ..scrape import Scrape_GUI
import pandas as pd
import numpy as np
import yfinance as yf
import logging
from ratelimit import limits, sleep_and_retry
import matplotlib.pyplot as plt


from pprint import pp

class Portfolio:
    
    def __init__(self, update=False):
        self.brokers = {}
        if update:
            Etrade('FRANK',update=update)
            Etrade('AMY',update=update)
            Fidelity(update=update)
        self.__get_portfolio()

    def get_broker_names(self):
        return sorted(self.brokers)

    def get_broker(self, name):
        if name in self.brokers:
            raise ValueError(f'Broker {name} does not exist')
        return self.brokers[name]

    def get_account_ids(self, broker_name=None):
        if isinstance(broker_name, type(None)):
            account_ids = []
            for broker_name, broker in self.brokers.items():
                account_ids += broker.get_account_ids()
            return account_ids
        else:
            if broker_name in  self.brokers:
                return self.brokers[broker_name].get_account_ids()
            else:
                raise ValueError(f'Broker {broker_name} does not exist')

    def get_accounts(self, broker_name=None):
        if isinstance(broker_name, type(None)):
            accounts = {}
            for broker_name, broker in self.brokers.items():
                accounts.update(broker.get_accounts())
            return accounts
        else:
            if broker_name in self.brokers:
                return self.brokers[broker_name].get_accounts()
            else:
                raise ValueError(f'Broker {broker_name} does not exist')

    def get_symbols(self, broker_name=None):
        symbols = set()
        if isinstance(broker_name, type(None)):
            for broker_name, broker in self.brokers.items():
                symbols.update(broker.get_symbols())
            return sorted(symbols)
        else:
            if broker_name in self.brokers:
                return self.brokers[broker_name].get_symbols()
            else:
                raise ValueError(f'Broker {broker_name} does not exist')
    
    def make_quicken_prices(self, date = None, add_symbols = []):
        ftime = FTime()
        symbols = set()
        for broker_name, broker in self.brokers.items():
            for account_id, account in broker.accounts.items():
                symbols.update(account.get_position_symbols())
        symbols.update(add_symbols)
        symbols = sorted(symbols)

        Scrape_GUI(symbols, settings=['yahoof_chart'])

        tickers = Tickers(symbols)
        charts = tickers.get_chart()

        if isinstance(date, type(None)):
            date = ftime.get_offset(ftime.now_naive, months=-1)
            date = ftime.get_month_end(date)
        else:
            date = ftime.get_date_naive(date)

        dftn = pd.Series()
        for symbol, chart in charts.items():
            price = chart[:date]
            if price.empty: continue
            price = price.iloc[-1]['adj_close']
            dftn[symbol] = price
    
        dftn = dftn.dropna().round(2)
        path = 'Z:\\Quicken\\Quicken_Import_%s.csv' % date.date()
        
        print(dftn)
        print(path)
        dftn.to_csv(path, header=False, sep=',', encoding='utf-8')

    def report_data(self):
        # info params to retrieve
        info_params = {
            'shortName': 'name',
            'quoteType': 'type',
            'sectorDisp': 'sector',
            'industryDisp': 'industry',
            'country': 'country',
        }
        keep_positions_columns = [
            'alloc_%',
            'cost',
            'value',
            'gain',
            'gain_%',
            'quantity',
            'price_buy',
            'price',
            'dividend',
            'dividend_%',
            'cap_gain',
            'cap_gain_%',
            'years',
        ]

        broker_reports = {}

        # make yfinance non verbose
        yflogger = logging.getLogger('yfinance')
        yflogger.disabled = True
        yflogger.propagate = False

        # get all symbols so we can get carts and info from yfinance
        symbols = set()
        for broker_name, broker in self.brokers.items():
            broker_reports[broker_name] = broker.get_report()
            for account_id, account_report in broker_reports[broker_name].items():
                symbols.update(account_report['positions'].index)
                symbols.update(account_report['history'])
        symbols = sorted(symbols)

        # get all yfinance data
        if USE_CACHE_DATA:
            yfinance_data = storage.load('portfolio_report_yf')
        else:
            yfinance_data = self.__get_yfinance_data(symbols)
            storage.save(yfinance_data, 'portfolio_report_yf')

        # get last Close price
        price = pd.Series(name='price')
        for symbol, yfinance_data_symbol in yfinance_data.items():
            chart = yfinance_data_symbol['chart']
            if not chart.empty:
                price[symbol] = chart.iloc[-1]['Close']

        # parse through all accounts
        for broker_name, broker_report in broker_reports.items():
            for account_id, account_report in broker_report.items():
                # description = account_report['description']
                # title_account = '%s: %s (%s)' % (broker_name, description, account_id)
                positions = account_report['positions']
                history = account_report['history']
                symbols_account = set(positions.index)
                symbols_account.update(history)

                history_chart = account_report['history_chart'] = {} # chart for each symbol
                compare_chart = account_report['compare_chart'] = {} # comparing chart parameters with all symbols
                history_chart_total_merged = pd.DataFrame() # to create total chart

                # go through all possible symbols in transactions history 
                for symbol, history_symbol in history.items():
                    # title_symbol = '%s: %s: %s (%s)' % (symbol, broker_name, description, account_id)

                    if not symbol in yfinance_data: continue

                    work_data = history_symbol.cumsum()
                    
                    is_in_position = symbol in positions.index
                    if is_in_position:
                        cost = -work_data['cost'].iloc[-1]
                        is_same_quantity = abs(positions.loc[symbol, 'quantity'] - work_data.iloc[-1]['quantity']) < 0.1
                        if not is_same_quantity:
                            # print('HISTORY INCOMPLETE !: %s' % title_symbol)
                            continue
                    else:
                        # dont use the ones with ending quantity no zero, since there are not in positions anymore
                        if work_data['quantity'].iloc[0] < 0 or work_data.shape[0] < 2:
                            # print('HISTORY INCOMPLETE !: %s' % title_symbol)
                            continue
                        cost = -work_data['cost'].iloc[-2]

                    # create history chart
                    history_chart_symbol = Portfolio.__get_history_chart(history_symbol, yfinance_data[symbol]['chart'], cost)
                    history_chart[symbol] = history_chart_symbol

                    # add to history chart total positions
                    if is_in_position:
                        history_chart_total_merged = history_chart_total_merged.merge(history_chart[symbol],
                            how='outer', left_index=True, right_index=True, suffixes=('', '_%s' % symbol))

                    # create compare chart
                    if not history_chart[symbol].empty:
                        for param in ['gain_%']:
                            if not param in compare_chart:
                                compare_chart[param] = pd.DataFrame()
                            param_series = history_chart[symbol][param]
                            param_series.name = symbol
                            compare_chart[param] = compare_chart[param].merge(param_series, how='outer', left_index=True, right_index=True)

                # create history chart total
                account_report['history_chart_total'] = pd.DataFrame()
                total_params = ['cost', 'value', 'dividend', 'cap_gain']
                if not history_chart_total_merged.empty:
                    history_chart_total_merged = history_chart_total_merged.ffill()
                    history_chart_total = []
                    for column in total_params:
                        sum_columns = [c for c in history_chart_total_merged.columns if c.startswith(column)]
                        summed_column = history_chart_total_merged[sum_columns].sum(axis=1)
                        summed_column.name = column
                        history_chart_total.append(summed_column)
                    history_chart_total = pd.DataFrame(history_chart_total).T
                    if not history_chart_total.empty:
                        history_chart_total['gain'] = history_chart_total['cost'] + history_chart_total['value']
                        history_chart_total['gain_%'] = (history_chart_total['gain'] / -history_chart_total['cost'].iloc[-1]) * 100
                        account_report['history_chart_total'] = history_chart_total

                # create info
                info = {}
                for symbol in symbols_account:
                    info_all = yfinance_data[symbol]['info']
                    info_symbol = {}
                    for param, param_name in info_params.items():
                        if param in info_all:
                            info_symbol[param_name] = info_all[param]
                    info[symbol] = info_symbol
                info = pd.DataFrame(info).T
                info.index.name = 'symbol'
                account_report['info'] = info

                # fix positions cost and alloc_%
                for symbol, position in positions.iterrows():
                    if not symbol in history_chart: continue
                    if history_chart[symbol].empty: continue
                    cost_delta = abs(position['cost'] + history_chart[symbol].iloc[-1]['cost'])
                    if cost_delta > 0.1:
                        positions.loc[symbol, 'cost'] = -history_chart[symbol].iloc[-1]['cost']
                        cost_total = positions['cost'].sum()
                        positions['alloc_%'] = (positions['cost'] / cost_total) * 100
                        positions.sort_values('cost', ascending=False, inplace=True)

                    quantity_delta = abs(position['quantity'] - history_chart[symbol].iloc[-1]['quantity'])
                    if quantity_delta > 0.1:
                        raise ValueError('position quantity does not match ! broker: %s - account: %s - symbol: %s' % (broker_name,account_id, symbol))
                
                # add additional data to positions
                positions = positions.merge(price, how='left', left_index=True, right_index=True)
                positions['value'] = positions['price'] * positions['quantity']
                positions['gain'] = positions['value'] - positions['cost']
                positions['gain_%'] = (positions['gain'] / positions['cost']) * 100
                history_merge = pd.DataFrame(columns=['dividend', 'cap_gain'])
                for symbol, history_symbol in account_report['history'].items():
                    history_merge.loc[symbol] = history_symbol.sum()
                positions = positions.merge(history_merge, how='left', left_index=True, right_index=True)
                positions['dividend_%'] = (positions['dividend'] / positions['cost']) * 100
                positions['cap_gain_%'] = (positions['cap_gain'] / positions['cost']) * 100
                keep_columns = [c for c in keep_positions_columns if c in positions.columns]
                positions = positions[keep_columns]
                account_report['positions'] = positions

                # create positions total
                positions_total = positions.sum()[['cost', 'value', 'gain', 'gain_%', 'dividend', 'cap_gain']]
                positions_total['gain_%'] = (positions_total['gain'] / positions_total['cost']) * 100
                account_report['positions_total'] = positions_total
        
        return broker_reports

    @staticmethod
    def __get_history_chart(history, chart, cost):
        if chart.empty: return pd.DataFrame()

        # get history starting chart
        chart = chart.copy()
        first_date = history.index[0]
        chart.index = chart.index.tz_localize(None) 
        chart = chart.loc[first_date:]

        # account for stocksplits on Close
        has_splits = chart['Stock Splits'] != 0.0
        if has_splits.any():
            stock_splits = chart['Stock Splits'].replace(0.0, 1.0)[::-1].cumprod()[::-1].shift(-1).ffill()
            chart['Open'] = chart['Open'] * stock_splits
            chart['Close'] = chart['Close'] * stock_splits
            chart['High'] = chart['High'] * stock_splits
            chart['Low'] = chart['Low'] * stock_splits
        
        # get cummulative history
        history_full = chart[['Close']].copy()
        # outer since some days the stock markets were closed (like death of Jimmy Carter)
        history_full = history_full.merge(history, how='outer', left_index=True, right_index=True).replace(np.nan, 0.0).cumsum()
        history_full['Close'] = chart['Close']
        history_full['Close'] = history_full['Close'].ffill() # for if any outer were added

        # add additional data
        history_full['value'] = history_full['Close'] * history_full['quantity']
        history_full['gain'] = history_full['cost'] + history_full['value']
        if cost == 0:
            history_full['gain_%'] = 0
        else:
            history_full['gain_%'] = (history_full['gain'] / cost) * 100

        return history_full

    @staticmethod
    def __dataframe_plot(df, title, ylabel='', line=0.0, figsize=(11, 6), dpi=100):
        df = df.dropna(axis=1, how='all')
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        df.plot(ax=ax, title=title, legend=False)
        for line2d in ax.get_lines():
            label = line2d.get_label()
            color = line2d.get_color()
            last_value = df[label].dropna()
            annotate_x = last_value.index[-1]
            annotate_y = last_value.values[-1]
            ax.annotate(label, xy=(annotate_x, annotate_y),
                fontsize=8, fontweight='bold', xytext=(2, 2), textcoords='offset points', color=color)
        ax.grid(True, linestyle='--', linewidth=0.5, color='gray')
        # ax.axhline(y=line, color='black', alpha=0.5, linestyle='--', linewidth=1)
        ax.set_ylabel(ylabel, fontweight='bold')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: '{:.0f}'.format(x)))
        plt.tight_layout()
        return fig
    
    def history_graphs(self):
        plt.style.use('tableau-colorblind10')
        report_data = self.report_data()
        for broker_name, broker_report in report_data.items():
            for account_id, account_report in broker_report.items():
                if 'gain_%' in account_report['compare_chart']:
                    description = account_report['description']
                    title_account = '%s: %s (%s)' % (broker_name, description, account_id)
                    compare_chart = account_report['compare_chart']['gain_%']
                    history_chart = account_report['history_chart']
                    positions = account_report['positions']

                    plot_chart = compare_chart.copy()
                    plot_chart.replace(0, np.nan, inplace=True)

                    # remove duplicates (lice when sold)
                    for column in plot_chart.columns:
                        # print(column)
                        temp = plot_chart[[column]].copy()
                        duplicates = plot_chart[column] == plot_chart[column].shift(1)
                        plot_chart[column].loc[duplicates] = np.nan
                    plot_chart = plot_chart.ffill(limit_area='inside')
                    print(plot_chart)
                    
                    self.__dataframe_plot(plot_chart, title_account, ylabel='gain %')
                    plt.show()

    def report(self):
        plt.style.use('tableau-colorblind10')
        report_data = self.report_data()
        report_path = 'Z:\\AALBERS-CHEN ASSETS\\Portfolio'
        r = Report(report_path, landscape=True)
        
        for broker_name, broker_report in report_data.items():
            for account_id, account_report in broker_report.items():
                description = account_report['description']
                title = '%s (%s, %s)' % (description, account_id, broker_name)
                positions = account_report['positions']
                positions_total = account_report['positions_total']
                positions_symbols = list(positions.index)
                info = account_report['info']
                compare_chart = account_report['compare_chart']
                
                r.add_paragraph(title, style=r.get_style('Heading2'))

                # add positions group
                r.add_paragraph('POSITIONS:', style=r.get_style('Heading5'), group=True)
                
                positions_table = positions.map('{:,.2f}'.format)
                r.add_table(positions_table.reset_index(), symbol_link=True, group=True)
                
                positions_totals_table = positions_total.map('{:,.2f}'.format).to_frame()
                positions_totals_table = positions_totals_table.rename(columns={0: 'TOTAL'}).T
                positions_totals_table.reset_index(inplace=True)
                positions_totals_table.rename(columns={'index': ''}, inplace=True)
                r.add_space(0.1, group=True)
                r.add_table(positions_totals_table, group=True)
                
                r.add_group()

                # add info group
                symbols_info = [s for s in positions_symbols if s in info.index]
                info_table = info.loc[symbols_info]
                info_table.reset_index(inplace=True)
                r.add_paragraph('SYMBOLS INFO:', style=r.get_style('Heading5'), group=True)
                r.add_table(info_table, allign='LEFT', symbol_link=True, group=True)
                r.add_paragraph('<a href="https://finviz.com/screener.ashx?v=110&t=%s" color="blue">COMPARE SYMBOLS</a>' % ( ','.join(positions_symbols)),
                    group=True)

                r.add_group()

                r.add_page_break()

                if 'gain_%' in compare_chart:
                    plot_data = compare_chart['gain_%']
                    plot_data = plot_data[[c for c in plot_data.columns if c in positions.index]].copy()
                    plot_data.replace(0, np.nan, inplace=True)

                    fig = self.__dataframe_plot(plot_data, title, ylabel='gain %', figsize=(11, 7), dpi=300)
                    r.add_plot_figure(fig)
                    r.add_page_break()

        r.build()

    def __get_portfolio(self):
        db = Database('portfolio')
        accounts = db.table_read('accounts')
        del(db)
        if accounts.empty: return
        for broker_name in accounts['broker'].unique():
            self.brokers[broker_name] = Broker(broker_name)

    @sleep_and_retry
    @limits(calls=50, period=60) # 6000 calls /hour , two calls in this function
    def __get_yfinance_data_symbol(self, symbol):
        data = {}
        ticker = yf.Ticker(symbol)
        try:
            data['info'] = ticker.info
        except:
            data['info'] = {}
            data['chart'] = pd.DataFrame()
            print('yfinance info failed: *%s*' % symbol)
            return data
        data['chart'] = ticker.history(period='10y',auto_adjust=False)
        return data

    def __get_yfinance_data(self, symbols):
        data = {}
        for symbol in symbols:
            data[symbol] = self.__get_yfinance_data_symbol(symbol)
        return data
