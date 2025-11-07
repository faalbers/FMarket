import pandas as pd
import numpy as np

def get_average(df, median_threshold=0.1):
    average = pd.DataFrame()
    average['mean'] = df.mean()
    average['median'] = df.median()
    average = average.T
    average.loc['deviation'] = np.abs(average.diff().iloc[-1]) / np.abs(average).max()
    average = average.T
    average.loc[average['deviation'] > median_threshold, 'average'] = average['median']
    average.loc[average['deviation'] <= median_threshold, 'average'] = average['mean']
    return average['average']

def get_trends(df, check_gaps=True):
    df = df.dropna(how='all', axis=0)

    trends = pd.DataFrame(columns=['last_valid_value', 'last_valid_index', 'step_count', 'step_growth', 'volatility'])
    for column in df.columns:
        # analyze per column
        column_data = df[column]

        last_valid_index = column_data.last_valid_index()
        if last_valid_index is None:
            trends.loc[column, 'last_valid_index'] = np.nan
            trends.loc[column, 'last_valid_value'] = np.nan
        else:
            trends.loc[column, 'last_valid_index'] = last_valid_index
            trends.loc[column, 'last_valid_value'] = column_data.loc[last_valid_index]

        # get data from first notna to last notna 
        column_data = column_data.loc[column_data.first_valid_index():column_data.last_valid_index()]

        # get last continues set of values based on index
        if check_gaps:
            column_data_check = column_data.dropna()
            index_range = column_data_check.index.to_series() - column_data_check.index.to_series().shift(1)
            start_values = (index_range > 1) | (index_range < -1)
            if start_values.any():
                column_data = column_data.loc[start_values.idxmax():]
            column_data.dropna(inplace=True)

        # # linear interpolate data for missing gaps
        # if fill_gaps:
        #     column_data = column_data.interpolate(method='linear')
        # elif column_data.isna().any():
        #     trends.loc[column] = np.nan
        #     continue

        # reset index for linear regression
        column_data = column_data.reset_index(drop=True)

        trends.loc[column, 'step_count'] = column_data.shape[0]

        if column_data.shape[0] >= 2:
            column_data
            coeffs = np.polyfit(column_data.index, column_data.values, 1)
            trend_past = np.polyval(coeffs, column_data.index)
            trend_future = np.polyval([coeffs[0], trend_past[-1]], column_data.index)
            if trend_future[0] != 0:
                trends.loc[column, 'step_growth'] = ((trend_future[1]-trend_future[0]) / np.abs(trend_future[0])) * 100.0
            # trend_future = trend_future[trend_future >= 0]
            # if trend_future.shape[0] >= 2:
            #     cagr = ((trend_future[-1] / trend_future[0]) ** (1 / (trend_future.shape[0] - 1))) - 1
            #     trends.loc[column, 'cagr'] = cagr * 100.0

            # calculate volatility
            residual_std = np.std(column_data.values - trend_past)
            trend_mean = trend_past.mean()
            if trend_mean != 0:
                trends.loc[column, 'volatility'] = (residual_std / np.abs(trend_mean)) * 100.0

    return trends
