import numpy as np
import pandas as pd
import scipy
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV
import matplotlib.pyplot as plt
from datetime import datetime
import talib as ta


# Checks if there is a local top detected at curr index
def rw_top(data: np.array, curr_index: int, order: int) -> bool:
    if curr_index < order * 2 + 1:
        return False

    top = True
    k = curr_index - order
    v = data[k]
    for i in range(1, order + 1):
        if data[k + i] > v or data[k - i] > v:
            top = False
            break
    
    return top

# Checks if there is a local top detected at curr index
def rw_bottom(data: np.array, curr_index: int, order: int) -> bool:
    if curr_index < order * 2 + 1:
        return False

    bottom = True
    k = curr_index - order
    v = data[k]
    for i in range(1, order + 1):
        if data[k + i] < v or data[k - i] < v:
            bottom = False
            break
    
    return bottom

def rw_extremes(data: np.array, order:int):
    # Rolling window local tops and bottoms
    tops = []
    bottoms = []
    for i in range(len(data)):
        if rw_top(data, i, order):
            # top[0] = confirmation index
            # top[1] = index of top
            # top[2] = price of top
            top = [i, i - order, data[i - order]]
            tops.append(top)
        
        if rw_bottom(data, i, order):
            # bottom[0] = confirmation index
            # bottom[1] = index of bottom
            # bottom[2] = price of bottom
            bottom = [i, i - order, data[i - order]]
            bottoms.append(bottom)
    
    return tops, bottoms    

def directional_change(close: np.array, high: np.array, low: np.array, sigma: float):
    up_zig = True # Last extreme is a bottom. Next is a top. 
    high_max = high[0]
    low_min = low[0]
    high_max_i = 0
    low_min_i = 0

    tops = []
    bottoms = []

    status = {}

    for i in range(len(close)):
        if up_zig: # Last extreme is a bottom
            confirmation_line = high_max - (high_max * sigma)
            if high[i] > high_max:
                # New high, update if after bottom extreme
                high_max = high[i]
                high_max_i = i
            elif close[i] < confirmation_line:
                # if new high is not created , check if close is lower then confirmation_line
                # if so , a new top extreme is confirmed on that index
                # the high max and it's index is created in that top extreme
                # that high max and it's index is the top extreme

                # print(i, close[i], high_max - high_max * sigma)
                # Price retraced by sigma %. Top confirmed, record it
                # top[0] = confirmation index
                # top[1] = index of top
                # top[2] = price of top
                top = [i, high_max_i, high_max]
                tops.append(top)

                # Setup for next bottom extreme
                up_zig = False
                low_min = low[i]
                low_min_i = i
        else: # Last extreme is a top
            confirmation_line = low_min + (low_min * sigma)
            if low[i] < low_min:
                # New low, update is after top extreme
                low_min = low[i]
                low_min_i = i
            elif close[i] > low_min + low_min * sigma: 
                # if new low is not created , check if close is higher then confirmation_line
                # if so , a new bottom extreme is confirmed on that index
                # the low min and it's index is created in that bottom extreme
                # that low max and it's index is the bottom extreme
                
                # Price retraced by sigma %. Bottom confirmed, record it
                # bottom[0] = confirmation index
                # bottom[1] = index of bottom
                # bottom[2] = price of bottom
                bottom = [i, low_min_i, low_min]
                bottoms.append(bottom)

                # Setup for next top
                up_zig = True
                high_max = high[i]
                high_max_i = i

    return tops, bottoms

def get_extremes(ohlc: pd.DataFrame, sigma: float):
    tops, bottoms = directional_change(ohlc['close'], ohlc['high'], ohlc['low'], sigma)
    tops = pd.DataFrame(tops, columns=['conf_i', 'ext_i', 'ext_p'])
    bottoms = pd.DataFrame(bottoms, columns=['conf_i', 'ext_i', 'ext_p'])
    tops['type'] = 1
    bottoms['type'] = -1
    extremes = pd.concat([tops, bottoms])
    extremes = extremes.set_index('conf_i')
    extremes = extremes.sort_index()
    return extremes

def find_level(prices_log: np.array, atr: float, first_w: float = 0.01, prom_thresh: float = 0.25):
    # get range
    prices_log_min = np.min(prices_log)
    prices_log_max = np.max(prices_log)
    price_log_range = prices_log_max - prices_log_min

    bandwith = price_log_range * atr * 180

    # sample weights
    first_w = 0.1
    last_w = 1.0
    w_step = (last_w - first_w) / len(prices_log)
    sample_weights = first_w + np.arange(len(prices_log)) * w_step
    sample_weights[sample_weights < 0] = 0.0

    # kde = scipy.stats.gaussian_kde(prices_log, bw_method=bandwith, weights=sample_weights)
    kde = scipy.stats.gaussian_kde(prices_log, bw_method='scott', weights=sample_weights)

    # Construct market profile
    price_log_linspace = np.linspace(prices_log_min, prices_log_max, 200)
    pdf = kde(price_log_linspace) # Market profile
    
    prom_min = np.max(pdf) * prom_thresh
    peaks, props = scipy.signal.find_peaks(pdf, prominence=prom_min)
    # peaks, props = scipy.signal.find_peaks(pdf)
    pdf_peak_max = 0.0
    price_log_peak = np.nan
    for peak in peaks:
        if pdf[peak] > pdf_peak_max:
            pdf_peak_max = pdf[peak]
            price_log_peak = price_log_linspace[peak]
    # # Find significant peaks in the market profile
    # pdf_max = np.max(pdf)
    # prom_min = pdf_max * prom_thresh

    # peaks, props = scipy.signal.find_peaks(pdf, prominence=prom_min)
    # levels = [] 
    # for peak in peaks:
    #     levels.append(np.exp(price_range[peak]))

    # fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]}, figsize=(10, 5))
    # plot_price = pd.Series(prices_log, name='price_log')
    # plot_price.plot(ax=ax1)
    # ax2.plot(pdf, price_log_linspace, label='pdf_1')
    # # ax2.plot(pdf_2, price_log_linspace, label='pdf_2')
    # # for peak in peaks:
    # #     ax1.axhline(price_log_linspace[peak], color='green', linestyle='--')
    # ax1.axhline(price_log_peak, color='green', linestyle='--')
    # plt.tight_layout()
    # plt.show()

    return price_log_peak

def frank_test(chart: pd.DataFrame, symbol):
    price_log = np.log(chart['Close'].values)
    price_log = price_log / 2.0
    price_log_sma = ta.SMA(price_log, timeperiod=14)
    price_log_sma_dropnan = price_log_sma[~np.isnan(price_log_sma)]

    bandwith = 0.05
    kde = scipy.stats.gaussian_kde(price_log_sma_dropnan, bw_method=bandwith)
    price_log_linspace = np.linspace(np.min(price_log), np.max(price_log), 200)
    # price_log_linspace = np.linspace(np.min(price_log_sma_dropnan), np.max(price_log_sma_dropnan), 200)
    pdf = kde(price_log_linspace) # Market profile

    prom_min = np.max(pdf) * 0.2
    peaks, props = scipy.signal.find_peaks(pdf, prominence=prom_min)

    # fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]}, figsize=(10, 5))
    # ax1.set_title(symbol)
    # ax1.plot(chart.index, price_log)
    # ax1.plot(chart.index, price_log_sma)
    # ax2.plot(pdf, price_log_linspace, label='pdf')
    # for peak in peaks:
    #     ax1.axhline(price_log_linspace[peak], color='green', linestyle='--')
    # plt.tight_layout()
    # plt.show()
    for peak in peaks:
        # price_log_peak = price_log_linspace[peak]
        # price_log_peak_diff = np.abs(price_log - price_log_peak)
        # fig, ax = plt.subplots(figsize=(10, 5))
        # ax.set_title(symbol)
        # ax.plot(chart.index, price_log_peak_diff)
        # ax.axhline(0, color='green', linestyle='--')
        # plt.tight_layout()
        # plt.show()
        # # break

        price_log_peak = price_log_linspace[peak]
        price_log_peak_diff = np.abs(price_log - price_log_peak)
        edge = np.max(price_log_peak_diff) * 0.10
        test = price_log_peak_diff[price_log_peak_diff < edge]
        edge = np.mean(test) * 2
        price_groups = pd.Series(price_log_peak_diff, index=chart.index).copy()
        price_groups[price_groups > edge] = np.nan
        price_groups = price_groups.ffill().bfill()

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.set_title(symbol)
        # ax.plot(chart.index, price_log_peak_diff)
        ax.plot(price_groups)
        ax.axhline(0, color='black', linestyle='--')
        # # ax.axhline(test_mean, color='orange', linestyle='--')
        # ax.axhline(edge, color='orange', linestyle='--')
        plt.tight_layout()
        plt.show()
        # break


def support_resist_levels(chart: pd.DataFrame, symbol):
    lookback = 14
    # Get log average true range, 
    atr = ta.ATR(np.log(chart['High'].values), np.log(chart['Low'].values), np.log(chart['Close'].values), timeperiod=lookback)
    atr = pd.Series(atr).bfill().to_numpy() # do a bfill to fill front missing in lookback
    
    # fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3,1]})
    # # fig, (ax1, ax2) = plt.subplots(2, 1)
    # ax1.plot(chart.index, chart['Close'].values)
    # ax1.set_title(symbol)
    # ax2.plot(chart.index, atr)
    # plt.tight_layout()
    # plt.show()

    # all_levels = [None] * len(data)
    # roll on lookback size
    price_levels = [np.nan] * (lookback-1)
    for i in range(lookback, chart.shape[0]+1):
        i_start  = i - lookback
        prices_log = np.log(chart['Close'].iloc[i_start:i].values)
        price_level = np.exp(find_level(prices_log, atr[i-1]))
        price_levels.append(price_level)

    price_levels = pd.Series(price_levels, index=chart.index, name='price_levels')
    plot_data = chart['Close'].to_frame()
    plot_data['price_levels'] = price_levels
    plot_data.plot()
    plt.show()

        

def frank_test_old(price: np.array, symbol):
    # price_log = np.log(price)

    # fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    # ax1.plot(range(len(price)), price)
    # ax1.set_title(symbol)
    # ax2.plot(range(len(price)), price_log)
    # plt.tight_layout()
    # plt.show()
    # return
    price_linspace = np.linspace(np.min(price), np.max(price), 200)

    price_range = np.max(price) - np.min(price)
    print(len(price), price_range)

    # sample weights
    first_w = 1.0
    last_w = 1.0
    w_step = (last_w - first_w) / len(price)
    sample_weights = first_w + np.arange(len(price)) * w_step
    sample_weights[sample_weights < 0] = 0.0

    price_sklearn = price.reshape(-1, 1)
    price_linspace_sklearn = price_linspace.reshape(-1, 1)

    bandwith_sklearn = price_range * 0.02

    bandwith_sklearn = bandwith_sklearn / 2
    start = datetime.now()
    kde_sklearn = KernelDensity(kernel='gaussian', bandwidth=bandwith_sklearn).fit(price_sklearn, sample_weight=sample_weights)
    # kde_sklearn = KernelDensity(kernel='gaussian', bandwidth=bandwith_sklearn).fit(price_sklearn)
    pdf_sklearn = np.exp(kde_sklearn.score_samples(price_linspace_sklearn))
    print(datetime.now() - start)

    price_scipy = price
    price_linspace_scipy = price_linspace

    bandwith_scipy = bandwith_sklearn / price_scipy.std(ddof=1)
    

    start = datetime.now()
    kde_scipy = scipy.stats.gaussian_kde(price_scipy, bw_method=bandwith_scipy, weights=sample_weights)
    # kde_scipy = scipy.stats.gaussian_kde(price_scipy, bw_method=bandwith_scipy)
    pdf_scipy = kde_scipy(price_linspace_scipy)
    print(datetime.now() - start)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, gridspec_kw={'width_ratios': [2, 1, 1]}, figsize=(15, 6))
    plot_price = pd.Series(price, name='price')
    plot_price.plot(ax=ax1, title=symbol)
    ax2.plot(pdf_sklearn, price_linspace)
    ax3.plot(pdf_scipy, price_linspace)
    plt.tight_layout()
    plt.show()


def find_levels_old( 
        price: np.array, atr: float, # Log closing price, and log atr 
        first_w: float = 0.1, 
        atr_mult: float = 3.0, 
        prom_thresh: float = 0.1
):

    # Setup weights
    last_w = 1.0
    w_step = (last_w - first_w) / len(price)
    weights = first_w + np.arange(len(price)) * w_step
    weights[weights < 0] = 0.0

    # Get kernel of price. 
    kernal = scipy.stats.gaussian_kde(price, bw_method=atr*atr_mult, weights=weights)

    # Construct market profile
    min_v = np.min(price)
    max_v = np.max(price)
    step = (max_v - min_v) / 200
    price_range = np.arange(min_v, max_v, step)
    pdf = kernal(price_range) # Market profile

    # Find significant peaks in the market profile
    pdf_max = np.max(pdf)
    prom_min = pdf_max * prom_thresh

    peaks, props = scipy.signal.find_peaks(pdf, prominence=prom_min)
    levels = [] 
    for peak in peaks:
        levels.append(np.exp(price_range[peak]))

    return levels, peaks, props, price_range, pdf, weights

def support_resistance_levels(
        data: pd.DataFrame, lookback: int, 
        first_w: float = 0.01, atr_mult:float=3.0, prom_thresh:float =0.25
):

    # Get log average true range, 
    atr = ta.atr(np.log(data['high']), np.log(data['low']), np.log(data['close']), lookback)

    all_levels = [None] * len(data)
    for i in range(lookback, len(data)):
        i_start  = i - lookback
        vals = np.log(data.iloc[i_start+1: i+1]['close'].to_numpy())
        levels, peaks, props, price_range, pdf, weights= find_levels(vals, atr.iloc[i], first_w, atr_mult, prom_thresh)
        all_levels[i] = levels
        
    return all_levels