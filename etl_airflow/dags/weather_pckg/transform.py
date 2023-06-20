import pandas as pd

def calculate_mean_avg_humidity(data):
    # Sort the data by date in ascending order
    data.sort_values('date', inplace=True)

    # Create a new column to store the mean of the previous 3 days' average humidity
    data['mean_avghumidity_3days'] = pd.Series(dtype='float64')

    # Iterate over each row in the dataframe
    for i, row in data.iterrows():
        if i >= 3:
            # Calculate the mean of the previous 3 days' average humidity
            mean_avg_humidity_3days = data.loc[i - 3:i - 1, 'avghumidity'].mean()
            data.at[i, 'mean_avghumidity_3days'] = mean_avg_humidity_3days

    return data['mean_avghumidity_3days']


def calculate_humidity_ratio(data):
    # Sort the data by date in ascending order
    data.sort_values('date', inplace=True)

    # Calculate the ratio of avg_humidity to the previous day's avg_humidity
    return data.loc[:, 'avghumidity'].pct_change().round(decimals=2)