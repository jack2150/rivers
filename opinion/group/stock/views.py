import json
import os
import time
import pandas as pd
import numpy as np
from django import forms

from base.ufunc import ts
from django.shortcuts import render
from data.get_data import GetData
from rivers.settings import QUOTE_DIR


def report_earning(request, symbol):
    """
    Earning report price move estimate
    :param request: request
    :param symbol: str
    :return: render
    """
    df_stock = GetData.get_stock_data(symbol)
    df_stock = df_stock.sort_index()
    closes = df_stock['close']
    volumes = df_stock['volume']

    df_earning = GetData.get_event_data(symbol, 'earning')
    df_earning = df_earning[df_earning['actual_date'] >= df_stock.index[0]]
    df_earning['diff'] = df_earning['adjusted_eps'] - df_earning['estimate_eps']

    try:
        df_iv = GetData.get_iv_data(symbol, 30)
        df_iv = df_iv.set_index('date')
        iv = df_iv['impl_vol']
    except KeyError:
        iv = []

    prices = []
    for index, data in df_earning.iterrows():
        if data['release'] == 'After Market':
            # after market: today & tomorrow
            date_index0 = closes.index.get_loc(data['actual_date'])
            date_index1 = date_index0 + 1
            date_index5r = date_index0 - 5
            date_index5 = date_index1 + 5
        else:
            # before market & between market: yesterday & today
            date_index0 = closes.index.get_loc(data['actual_date']) - 1
            date_index1 = date_index0 + 1
            date_index5r = date_index0 - 5
            date_index5 = date_index1 + 5

        day_iv = None
        if len(iv):
            day_iv = GetData.calc_day_iv(iv[date_index0], 30, 1)

        prices.append({
            'actual_date': data['actual_date'],
            'prev5d': closes[closes.index[date_index5r]],
            'date0': closes.index[date_index0].strftime('%Y-%m-%d'),
            'close0': closes[closes.index[date_index0]],
            'date1': closes.index[date_index1].strftime('%Y-%m-%d'),
            'close1': closes[closes.index[date_index1]],
            'next5d': closes[closes.index[date_index5]],
            'volume': volumes[closes.index[date_index0]],
            'day_iv': day_iv
        })

    df_earning2 = pd.DataFrame(prices)
    df_earning2.set_index('actual_date')
    df_data = pd.merge(df_earning, df_earning2, on='actual_date')
    """:type: pd.DataFrame"""

    df_data['diff%'] = (df_data['diff'] / df_data['estimate_eps']) * 100
    df_data['day%'] = (df_data['close1'] / df_data['close0'] - 1) * 100
    df_data['prev5d%'] = (df_data['prev5d'] / df_data['close0'] - 1) * 100
    df_data['next5d%'] = (df_data['next5d'] / df_data['close1'] - 1) * 100
    if len(iv):
        df_data['within_iv'] = df_data['day_iv'] >= np.abs(df_data['day%'])
        df_data['within_iv'] = df_data['within_iv'].apply(lambda x: 'Yes' if x else 'No')
    else:
        del df_data['day_iv']

    df_data = df_data.round(2)
    # ts(df_data)

    # describe data
    report = []
    sub_data = {
        # bull/bear
        'bull': df_data[df_data['day%'] > 0],
        'bear': df_data[df_data['day%'] < 0],

        # earning estimate
        'beat': df_data[df_data['adjusted_eps'] > df_data['est_high']],
        'meet': df_data[
            (df_data['adjusted_eps'] >= df_data['est_low']) &
            (df_data['adjusted_eps'] <= df_data['est_high'])
        ],
        'miss': df_data[df_data['adjusted_eps'] < df_data['est_low']],

    }

    for key in ('beat', 'meet', 'miss', 'bull', 'bear'):
        data = sub_data[key]
        temp = {
            'name': key.capitalize(),
            'count': len(data),
            'median': data['day%'].median(),
            'std': round(data['day%'].std(), 2),
            'mean_cap': round((data['volume'] * data['close1']).mean())
        }

        for name in ('count', 'median', 'std', 'mean_cap'):
            temp[name] = 0 if np.isnan(temp[name]) else temp[name]

        temp['mean_cap'] = int(temp['mean_cap'])
        report.append(temp)

    # make json
    est_hl = []
    est_mean = []
    price_move = []
    for index, data in df_data.iterrows():
        dt = time.mktime(data['actual_date'].to_datetime().timetuple()) * 1000
        est_hl.append([
            dt,
            round((data['est_low'] / data['estimate_eps'] - 1) * 100, 2),
            round((data['est_high'] / data['estimate_eps'] - 1) * 100, 2)
        ])
        est_mean.append([
            dt,
            round((data['adjusted_eps'] / data['estimate_eps'] - 1) * 100, 2)
        ])
        price_move.append([
            dt,
            round((data['close1'] / data['close0'] - 1) * 100, 2)
        ])

    # print est_hl

    json_data = {
        'est_hl': est_hl[:12],
        'est_mean': est_mean[:12],
        'price_move': price_move[:12]
    }

    # json table
    json_table = []
    for index, data in df_data.iterrows():
        data['actual_date'] = data['actual_date'].to_datetime().strftime('%Y-%m-%d')
        json_table.append(dict(data))

    # print json_table

    title = 'Earning report | %s' % symbol.upper()
    template = 'opinion/stock/earning/report.html'
    parameters = dict(
        site_title=title,
        title=title,
        symbol=symbol,
        json_data=json_data,
        df_data=json.dumps(json_table),
        df_report=json.dumps(report),
        iv=len(iv) > 0,
    )

    return render(request, template, parameters)
