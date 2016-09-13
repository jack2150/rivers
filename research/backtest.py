import django

django.setup()

import click
import os
import pandas as pd
from rivers.settings import RESEARCH_DIR
from django.db.models import Q
from research.algorithm.models import Formula, FormulaResult
from research.strategy.backtest import TradeBacktest
from research.strategy.models import Trade, TradeResult


@click.group()
def backtest():
    pass


@backtest.command()
@click.option('--symbol', help='Symbol name', required=True)
@click.option('--formula_id', help='Formula ID', required=True)
@click.option('--start', help='Start date', required=True)
@click.option('--stop', help='Stop date', required=True)
@click.option('--fields', help='Arguments to be use', required=True)
def algorithm(symbol, formula_id, start, stop, fields):
    formula = Formula.objects.get(id=formula_id)
    click.echo('Backtest algorithm formula: %s symbol: %s' % (formula, symbol.upper()))
    click.echo('-' * 70)

    exec('fields = %s' % fields)

    date = pd.datetime.today().date()

    formula_result = FormulaResult.objects.filter(
        Q(symbol=symbol.upper()) & Q(date=date) & Q(formula=formula)
    )
    if formula_result.exists():
        raise AssertionError('Duplicated. Please remove old formula result.')

    formula.start_backtest()
    length = formula.backtest.save(fields, symbol, start, stop)

    # save formula result
    formula_result = FormulaResult(
        symbol=symbol.upper(),
        date=date,
        formula=formula,
        arguments=fields,
        length=length
    )
    formula_result.save()


@backtest.command()
@click.option('--symbol', required=True)
@click.option('--date', required=True)
@click.option('--formula_id', required=True)
@click.option('--report_id', required=True)
@click.option('--trade_id', required=True)
@click.option('--commission_id', required=True)
@click.option('--capital', required=True)
@click.option('--fields', required=True)
def strategy(symbol, date, formula_id, report_id, trade_id, commission_id, capital, fields):
    trade = Trade.objects.get(id=trade_id)
    formula = Formula.objects.get(id=formula_id)
    report_id = int(report_id)

    exec ('fields = %s' % fields)

    click.echo('Backtest strategy trade: %s symbol: %s' % (trade, symbol.upper()))
    click.echo('-' * 70)

    db = pd.HDFStore(os.path.join(RESEARCH_DIR, '%s.h5' % symbol.lower()))
    df_report = db.select('algorithm/report', where='formula == %r & date == %r' % (
        formula.path, date
    ))
    report = df_report.ix[report_id]
    df_signal = db.select(
        'algorithm/signal',
        where='formula == %r & date == %r & hd == %r & cs == %r' % (
            report['formula'], date, report['hd'], report['cs']
        )
    )
    db.close()

    trade_bt = TradeBacktest(symbol, trade)
    length = trade_bt.save(
        fields=fields,
        formula_id=int(formula_id),
        report_id=report_id,
        commission_id=int(commission_id),
        capital=int(capital),
        df_signal=df_signal
    )

    # save formula result
    formula_result = TradeResult(
        symbol=symbol.upper(),
        date=date,
        formula_id=formula.id,
        report_id=report_id,
        trade=trade,
        arguments=fields,
        length=length
    )
    formula_result.save()

if __name__ == '__main__':
    # sleep(10)
    backtest()
