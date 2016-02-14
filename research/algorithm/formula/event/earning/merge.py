import numpy as np
import pandas as pd


def merge_stock_earning(df_stock, df_earning):
    """

    :param df_stock:
    :param df_earning:
    :return:
    """
    df_earning2 = df_earning.sort_values('actual_date').copy()
    effect_dates = []
    for date, release in zip(df_earning2['actual_date'], df_earning2['release']):
        index = df_stock[df_stock['date'] == date].index
        if len(index):
            if release == 'After Market':
                effect_dates.append(index[0] + 1)
            else:
                effect_dates.append(index[0])
        else:
            effect_dates.append(np.nan)

    df_earning2['index'] = effect_dates
    df_earning2 = df_earning2.dropna('index')
    df_earning2 = df_earning2.set_index('index')

    # print df_earning2.to_string(line_width=1000)
    df2 = pd.concat([df_stock, df_earning2], join='outer', axis=1)
    """:type: pd.DataFrame"""
    # print df2[~df2['actual_date'].isnull()].to_string(line_width=1000)

    return df2.copy()
