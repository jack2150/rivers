from django.shortcuts import render
from StringIO import StringIO
import pandas as pd
from quantitative.models import AlgorithmResult
from simulation.models import StrategyResult


def df_html_view(request, result, result_id):
    """
    Dataframe view in html
    :param request: request
    :param result: str ('algorithm', 'strategy')
    :param result_id: int
    :return: render
    """
    if result == 'strategy':
        r = StrategyResult.objects.get(id=result_id)
        df = r.df_trade
        name = r.strategy.name
        args = r.arguments
    elif result == 'algorithm':
        r = AlgorithmResult.objects.get(id=result_id)
        df = r.df_signal
        name = r.algorithm.rule
        args = r.arguments
    else:
        raise ValueError('Result type can only be "strategy" or "algorithm"')

    df = pd.read_csv(StringIO(df), index_col=0)

    data = list()
    columns = list(df.columns)
    for index, trade in df.iterrows():
        data.append({c: trade[c] for c in columns})

    template = 'base/df_to_html/index.html'
    parameters = dict(
        site_title='Dataframe html view',
        title='{result} Result: {name}, Arg: {args}'.format(
            result=result.capitalize(), name=name, args=args
        ),
        data=data,
        columns=columns
    )

    return render(request, template, parameters)


