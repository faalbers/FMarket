import pandas as pd
import numpy as np
from scipy import stats

from ..utils import Plot

def get_trend(df):
    """
    Compare short and long-term moving averages.
    df must have a 'close' column.
    """
    df = df.copy()
    df.reset_index(inplace=True)
    df['sma_short'] = df['Close'].rolling(window=7*2).mean()
    df['sma_long'] = df['Close'].rolling(window=7*2*4).mean()
    
    
    current_price = df['Close'].iloc[-1]
    short_ma = df['sma_short'].iloc[-1]
    long_ma = df['sma_long'].iloc[-1]
    
    if short_ma > long_ma and current_price > short_ma:
        print ('uptrend')
    elif short_ma < long_ma and current_price < short_ma:
        print ('downtrend')
    else:
        print ('sideways')
    
    # plot = Plot(reset_index=True, annotate=True)
    # plot.plot(df[['Close', 'sma_short', 'sma_long']])
    # plot.show()


def get_trend_hl(df, lookback=20):
    """
    Check if making higher highs (uptrend) or lower lows (downtrend).
    df must have 'high' and 'low' columns.
    """
    recent_high = df['High'].iloc[-lookback:].max()
    recent_low = df['Low'].iloc[-lookback:].min()
    
    prev_high = df['High'].iloc[-lookback*2:-lookback].max()
    prev_low = df['Low'].iloc[-lookback*2:-lookback].min()
    
    if recent_high > prev_high and recent_low > prev_low:
        return 'uptrend'
    elif recent_high < prev_high and recent_low < prev_low:
        return 'downtrend'
    else:
        return 'sideways'

def get_trend_slope(df):
    pass

def get_trend_slope_old(df):
    """Returns trend direction and slope strength."""
    x = np.arange(len(df))
    y = df['Close'].values
    
    slope, intercept, r_value, _, _ = stats.linregress(x, y)
    
    threshold = 0.002  # Adjust based on your data
    if slope > threshold:
        return 'uptrend', slope
    elif slope < -threshold:
        return 'downtrend', slope
    else:
        return 'sideways', slope

def plot_hourly_column(dfs):
    fig, axs = plt.subplots(3, 1, gridspec_kw={'height_ratios': [0.5, 0.5, 2.5]}, sharex=True, figsize=(10, 8))
    for ax in axs:
        ax.xaxis.set_major_locator(plt_ticker.MultipleLocator(7*5*4))
        ax.xaxis.set_minor_locator(plt_ticker.MultipleLocator(7*5))
        ax.grid(True, linestyle='--', linewidth=1.0, color='gray', which='major', alpha=0.7)
        ax.grid(True, linestyle='--', linewidth=0.5, color='gray', which='minor', alpha=0.5)

