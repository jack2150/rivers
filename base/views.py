from StringIO import StringIO

import pandas as pd
from django.shortcuts import render

from research.algorithm.models import AlgorithmResult
from simulation.models import StrategyResult


# noinspection PyShadowingBuiltins
def df_view(request, model, id):
    if model == 'strategy':
        r = StrategyResult.objects.get(id=id)
        df = r.df_trade
        name = r.strategy.name
        args = r.arguments
    elif model == 'algorithm':
        r = AlgorithmResult.objects.get(id=id)
        df = r.df_signal
        name = r.algorithm.rule
        args = r.arguments
    else:
        raise ValueError('Result type can only be "strategy" or "algorithm"')

    df = pd.read_csv(StringIO(df), index_col=0)
    """:type: DataFrame"""
    df['date0'] = df['date0'].astype('datetime64').apply(lambda x: x.to_datetime().date())
    df['date1'] = df['date1'].astype('datetime64').apply(lambda x: x.to_datetime().date())

    df.index = range(len(df))
    df = df.sort(['date0'], ascending=[False])

    df = df[[
        'date0', 'date1', 'signal0', 'signal1', 'close0', 'close1', 'holding',
        'mean', 'median', 'max', 'min', 'std', 'max2', 'min2', 'p_pct', 'l_pct',
        'pct_chg'
    ]]

    template = 'base/df_view/index.html'

    parameters = dict(
        site_title='Dataframe view',
        title='< {symbol} > {result} Result: {name}, Arg: {args}'.format(
            symbol=r.symbol, result=model.capitalize(), name=name, args=args
        ),
        df=df.to_string(line_width=700),
        model=model,
    )

    return render(request, template, parameters)
