import click
import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rivers.settings")

from rivers.settings import RESEARCH_DIR
from research.algorithm.models import Formula, FormulaResult
from research.strategy.backtest import TradeBacktest
from research.strategy.models import Trade


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

    formula.start_backtest()
    length = formula.backtest.save(fields, symbol, start, stop)

    # save formula result
    formula_result = FormulaResult(
        symbol=symbol.upper(),
        formula=formula,
        date=pd.datetime.today().date(),
        arguments=fields,
        length=length
    )
    formula_result.save()

    click.pause()


@backtest.command()
@click.option('--symbol', required=True)
@click.option('--formula_id', required=True)
@click.option('--backtest_id', required=True)
@click.option('--trade_id', required=True)
@click.option('--commission_id', required=True)
@click.option('--capital', required=True)
@click.option('--fields', required=True)
def strategy(symbol, formula_id, backtest_id, trade_id, commission_id, capital, fields):
    trade = Trade.objects.get(id=trade_id)
    formula = Formula.objects.get(id=formula_id)

    exec ('fields = %s' % fields)

    click.echo('Backtest strategy trade: %s symbol: %s' % (trade, symbol.upper()))
    click.echo('-' * 70)

    db = pd.HDFStore(os.path.join(RESEARCH_DIR, '%s.h5' % symbol.lower()))
    df_report = db.select('algorithm/report', where='formula == %r' % formula.path)
    report = df_report.iloc[0]
    df_signal = db.select('algorithm/signal', where='formula == %r & hd == %r & cs == %r' % (
        report['formula'], report['hd'], report['cs']
    ))
    db.close()

    trade_bt = TradeBacktest(symbol, trade)
    trade_bt.save(
        fields=fields,
        formula_id=int(formula_id),
        backtest_id=int(backtest_id),
        commission_id=int(commission_id),
        capital=int(capital),
        df_signal=df_signal
    )

if __name__ == '__main__':
    # sleep(10)
    backtest()
