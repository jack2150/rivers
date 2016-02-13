import click
import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rivers.settings")

from research.algorithm.models import Formula, FormulaResult


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


if __name__ == '__main__':
    # sleep(10)
    backtest()
