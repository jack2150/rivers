from fractions import Fraction

import re
from QuantLib import Option
from django.db.models import Q
from data.models import SplitHistory
from data.plugin.clean import run_clean, mass_extract_codes
from data.plugin.clean.clean import CleanOption, extract_code, get_div_yield
from django.shortcuts import render, redirect
import numpy as np
import pandas as pd
from rivers.settings import QUOTE

output = '%-6s | %-30s %s'


def clean_split_option(request, symbol):
    """
    Clean split or bonus issues option data
    :param request: request
    :param symbol: str
    :return: render
    """
    print output % ('SYMBOL', 'Running clean split/bonus option', symbol.upper())

    db = pd.HDFStore(QUOTE)
    df_rate = db.select('treasury/RIFLGFCY01_N_B')  # series
    df_rate = df_rate['rate']
    df_stock = db.select('stock/thinkback/%s' % symbol.lower())
    df_stock = df_stock['close']
    df_contract0 = db.select('option/%s/raw/contract' % symbol.lower())
    # df_contract1 = db.select('option/%s/clean/contract' % symbol.lower())
    df_option = db.select('option/%s/raw/data' % symbol.lower())
    df_option = df_option.reset_index().sort_values('date')
    try:
        df_dividend = db.select('event/dividend/%s' % symbol.lower())
        df_div = get_div_yield(df_stock, df_dividend)
    except KeyError:
        df_div = pd.DataFrame()
        df_div['date'] = df_stock.index
        df_div['amount'] = 0.0
        df_div['div'] = 0.0
    db.close()

    # get split history
    start, stop = df_option['date'].min(), df_option['date'].max()
    split_history = SplitHistory.objects.filter(
        Q(symbol=symbol.upper()) &
        Q(date__gte=start) & Q(date__lte=stop)
    ).order_by('date').reverse()
    # print split_history

    # get split only contract
    df_split = df_contract0.query('right != "100" & others == "" & special != "Mini"')
    # df_split = df_split[~df_split['option_code'].isin(df_contract1['option_code'])]
    print output % ('TOTAL', 'df_split length:', len(df_split))
    print df_contract0['right'].unique()

    if len(df_split):
        # print df_split.to_string(line_width=1000)
        df_all = pd.merge(df_option, df_split, how='inner', on='option_code').sort_values(
            ['option_code', 'date']
        )
        df_all = pd.merge(df_all, df_stock.reset_index(), how='inner', on=['date'])
        df_all = pd.merge(df_all, df_rate.reset_index(), how='inner', on=['date'])
        df_all = pd.merge(df_all, df_div.reset_index(), how='inner', on=['date'])
        del df_all['index']
        print output % ('TOTAL', 'df_all length:', len(df_all))

        df_all['close1'] = df_all['close']

        # multiply split to close price
        for i, c in df_split.iterrows():
            print output % ('SPLIT', 'Update close price by split:', c['option_code'])
            dates = df_all[df_all['option_code'] == c['option_code']]['date']
            date0, date1 = dates.min(), dates.max()
            # print date0, date1
            split = split_history.get(
                Q(fraction=c['right']) & Q(date__gte=date0) & Q(date__lte=date1)
            )

            if '/' in str(split.fraction):
                # split share, example: 1 for 20
                multiply = Fraction(split.fraction)
            else:
                # bonus issue like 150 close price is already adjust
                multiply = float(split.fraction) / 100.0

            df_all.loc[
                (df_all['option_code'] == c['option_code']) & (df_all['date'] >= split.date),
                'close1'
            ] *= multiply
            # print df_all[df_all['option_code'] == c['option_code']].sort_values('date').to_string(line_width=1000)

        # round two decimal
        df_all['close1'] = np.round(df_all['close1'], 2)

        # clean those option
        df_all = df_all.reset_index(drop=True)
        names = df_all['name'].apply(lambda n: 1 if n == 'CALL' else -1)
        results = run_clean(
            df_all['ex_date'],
            names,
            df_all['strike'],
            df_all['date'],
            df_all['rate'],
            df_all['close1'],
            df_all['bid'],
            df_all['ask'],
            df_all['impl_vol'],
            df_all['div']
        )

        df_result = pd.DataFrame(results)
        df_result.columns = [
            'impl_vol', 'theo_price', 'intrinsic', 'extrinsic',
            'dte', 'prob_itm', 'prob_otm', 'prob_touch',
            'delta', 'gamma', 'theta', 'vega'
        ]
        df_clean = df_all[['date', 'ask', 'bid', 'last', 'mark', 'open_int', 'option_code', 'volume']]
        df_clean = pd.concat([df_clean, df_result], axis=1)
        """:type: pd.DataFrame"""
        df_clean = df_clean.set_index('date')

        print df_clean.head().to_string(line_width=1000)

        # print df_all[df_all['option_code'] == 'AIG1090821P4'].to_string(line_width=1000)
        # print df_clean[df_clean['option_code'] == 'AIG1090821P4'].to_string(line_width=1000)

        # todo: append into clean table
        # todo: fillna support split
        # todo: what about bonus issues? 150
        # todo: follow new split strike format AAPL140613C70.71
        # todo: AAPL140613C495 -> AAPL140613C70.71

        #db = pd.HDFStore(QUOTE)
        #db.append('option/%s/clean/contract' % symbol.lower(), df_split)
        #db.append('option/%s/clean/data' % symbol.lower(), df_clean)
        #db.close()
    else:
        # no split contract
        print output % ('EMPTY', 'No split contract found', '')

    return redirect('admin:data_underlying_changelist')

# todo: create a view for split date
# todo: find bonus issus symbol


def merge_split_data(request, symbol):
    """

    :param request:
    :param symbol:
    :return:
    """
    print output % ('SYMBOL', 'Running merge split/bonus option', symbol.upper())

    db = pd.HDFStore(QUOTE)
    df_rate = db.select('treasury/RIFLGFCY01_N_B')  # series
    df_rate = df_rate['rate']
    df_stock = db.select('stock/thinkback/%s' % symbol.lower())
    df_stock = df_stock['close']
    df_contract = db.select('option/%s/raw/contract' % symbol.lower())
    # df_contract1 = db.select('option/%s/clean/contract' % symbol.lower())
    df_option = db.select('option/%s/raw/data' % symbol.lower())
    df_option = df_option.reset_index().sort_values('date')
    try:
        df_dividend = db.select('event/dividend/%s' % symbol.lower())
        df_div = get_div_yield(df_stock, df_dividend)
    except KeyError:
        df_div = pd.DataFrame()
        df_div['date'] = df_stock.index
        df_div['amount'] = 0.0
        df_div['div'] = 0.0
    db.close()

    # todo: DDD1130817P60 problem wrong merge
    # todo: remake import raw
    print df_option[df_option['option_code'] == 'DDD1130817P60'].to_string(line_width=1000)

    split_history = SplitHistory.objects.filter(Q(symbol=symbol.upper())).order_by('date').reverse()

    dates = pd.Series(df_option['date'].unique()).sort_values()
    #print dates
    group = df_option.groupby('option_code')
    date0, date1 = group['date'].min(), group['date'].max()

    for split in split_history:
        print split

        print dates[dates < split.date].iloc[-1]
        until = date1[date1 == dates[dates < split.date].iloc[-1]]  # before split date
        cont = date0[date0 == split.date]

        df_until = df_contract[df_contract['option_code'].isin(until.index)]
        df_cont = df_contract[df_contract['option_code'].isin(cont.index)]

        print len(until)
        print len(cont)
        #print until
        for i in cont.index:
            print i

        for code in until.index:
            print code
            c = df_until[df_until['option_code'] == code].iloc[0]

            new_strike = np.round(c['strike'] * Fraction(split.fraction), 2)
            if new_strike == int(new_strike):
                new_strike = int(new_strike)


            print c['strike'], '->', new_strike

            # todo: new option_code with strike, problem extra...
            new_code = '{symbol}{extra}{date_name}{strike}'.format(
                symbol=re.search('^([A-Z]+)\d+[CP]+\d+', code).group(1),
                extra=1,
                date_name=re.search('^[A-Z]+(\d+[CP]+)\d+', code).group(1),
                strike=new_strike
            )


            df_current = df_cont[df_cont['option_code'] == new_code]
            if len(df_current):
                #print df_current
                print new_code, 'found'
            else:
                print new_code, 'not'
            print '.' * 100





    return redirect('admin:data_underlying_changelist')