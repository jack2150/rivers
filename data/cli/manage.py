from data.plugin.raw2.views import ExtractOption
import click
import pandas as pd

from rivers.settings import QUOTE


@click.group()
def manage():
    pass


@manage.command()
@click.option('--symbol', help='Symbol of raw data.')
def create_raw(symbol):
    click.echo('Create raw data for: %s' % symbol)
    db = pd.HDFStore(QUOTE)
    df_stock = db.select('stock/thinkback/%s' % symbol.lower())
    db.close()

    extract_option = ExtractOption(symbol, df_stock)
    extract_option.start()

    click.pause()


@manage.command()
def valid_raw():
    click.echo('Dropped the database')
    click.pause()


if __name__ == '__main__':
    # sleep(10)
    manage()
