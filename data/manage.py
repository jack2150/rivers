import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rivers.settings")

import click
import pandas as pd
import time
from data.tb.valid.options import ValidRawOption
from data.tb.clean import CleanNormal
from datetime import timedelta
from subprocess import PIPE
from subprocess import Popen
from data.tb.raw.options import RawOption
from data.tb.raw.stocks import extract_stock
from data.tb.clean.split_new import CleanSplitNew
from data.tb.clean.split_old import CleanSplitOld
from data.tb.revalid.options import ValidCleanOption
from data.tb.fillna.normal import FillNaNormal
from data.tb.fillna.split_new import FillNaSplitNew
from data.tb.fillna.split_old import FillNaSplitOld
from data.tb.final.views import merge_final
from rivers.settings import QUOTE_DIR, CLEAN_DIR
from data.option.day_iv.cli import write_weekday_cli, import_weekday_cli
from data.option.day_iv.day_iv import DayIVCalc


@click.group()
def manage():
    pass


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of stock data.')
def import_stock(symbol):
    proc_stock(symbol)
    click.pause()


def proc_stock(symbol):
    click.echo('Import thinkback stock data: %s' % symbol.upper())
    extract_stock(symbol)


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of raw option data.')
def prepare_raw(symbol):
    proc_raw(symbol)
    click.pause()


def proc_raw(symbol):
    click.echo('Create raw data for: %s' % symbol.upper())
    path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
    print 'get df_stock from path: %s' % path
    db = pd.HDFStore(path)
    df_stock = db.select('stock/thinkback')
    db.close()
    # run import raw option
    extract_option = RawOption(symbol, df_stock)
    extract_option.start()
    extract_option.update_underlying()


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of valid raw options.')
def valid_raw(symbol):
    proc_valid_raw(symbol)
    click.pause()


def proc_valid_raw(symbol):
    click.echo('Valid raw data for: %s' % symbol.upper())
    # run valid raw option
    valid_option = ValidRawOption(symbol)
    valid_option.start()
    valid_option.update_underlying()


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of stock data.')
@click.option('--name', prompt='Name', help='(normal, others, split/old, split/new)')
def write_valid(symbol, name):
    if name == 'normal':
        clean_option = CleanNormal(symbol)
        clean_option.get_merge_data()
        lines = clean_option.to_csv().split()
    elif name == 'split/new':
        clean_option = CleanSplitNew(symbol)
        clean_option.get_merge_data()
        lines = clean_option.to_csv().split()
    elif name == 'split/old':
        clean_option = CleanSplitOld(symbol)
        clean_option.get_merge_data()
        clean_option.update_split_date()
        lines = clean_option.to_csv().split()
    else:
        raise KeyError('No DataFrame for "%s"' % name)

    for line in lines:
        click.echo(line)


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of stock data.')
@click.option('--name', prompt='Name', help='(normal, others, split/old, split/new)')
def read_clean(symbol, name):
    proc_clean(symbol, name)
    click.pause()


def proc_clean(symbol, name):
    click.echo('Clean %s data for: %s' % (name, symbol.upper()))
    path = os.getcwd().replace('\\', '/')
    cmd = r'{writer} | {reader}'.format(
        writer=r'python "{path}/data/manage.py" write_valid'
               r' --symbol={symbol} --name={name}'.format(path=path, symbol=symbol, name=name),
        reader=r'"{path}/data/tb/clean/clean.exe"'.format(path=path)
    )
    print 'cmd: %s' % cmd
    process = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    lines = []
    start_time = time.time()
    while True:
        line = process.stdout.readline()
        if line != '':
            # print line
            lines.append(line)

            if len(lines) % 1000 == 0:
                p_time = timedelta(seconds=(time.time() - start_time))
                print 'Time', str(p_time).split('.')[0], 'Records:', len(lines)
        else:
            break
    p_time = timedelta(seconds=(time.time() - start_time))
    print 'Time', str(p_time).split('.')[0], 'Records:', len(lines)

    # save data
    if name == 'normal':
        clean_option = CleanNormal(symbol)
        clean_option.get_merge_data()
        clean_option.save_clean(lines)
        clean_option.update_underlying()
    elif name == 'split/new':
        clean_option = CleanSplitNew(symbol)
        clean_option.get_merge_data()
        clean_option.save_clean(lines)
        clean_option.update_underlying()
    elif name == 'split/old':
        clean_option = CleanSplitOld(symbol)
        clean_option.get_merge_data()
        clean_option.save_clean(lines)
        clean_option.update_underlying()
    else:
        raise KeyError('No DataFrame for "%s"' % name)


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of valid raw options.')
def valid_clean(symbol):
    proc_valid_clean(symbol)
    click.pause()


def proc_valid_clean(symbol):
    click.echo('Valid clean data for: %s' % symbol.upper())
    # run valid raw option
    valid_option = ValidCleanOption(symbol)
    valid_option.start()
    valid_option.update_underlying()


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of stock data.')
@click.option('--name', prompt='Name', help='(normal, others, split/old, split/new)')
def fillna_missing(symbol, name):
    proc_fillna(symbol, name)
    click.pause()


def proc_fillna(symbol, name):
    name = name.lower()
    click.echo('Fill missing clean symbol: %s, name: %s' % (symbol.upper(), name))
    # run valid raw option
    if name == 'normal':
        fillna_clean = FillNaNormal(symbol)
    elif name == 'split/new':
        fillna_clean = FillNaSplitNew(symbol)
    elif name == 'split/old':
        fillna_clean = FillNaSplitOld(symbol)
    else:
        raise KeyError('No fillna for data: %s' % name)
    fillna_clean.save()
    fillna_clean.update_underlying()


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of stock data.')
def import_option(symbol):
    symbol = symbol.lower()
    proc_stock(symbol)
    proc_raw(symbol)
    proc_valid_raw(symbol)

    path = os.path.join(CLEAN_DIR, '__%s__.h5' % symbol.lower())
    db = pd.HDFStore(path)
    keys = list(db.keys())
    names = []
    for name in ('normal', 'split/new', 'split/old'):
        path = '/option/valid/%s' % name
        if path in keys:
            names.append(name)
    db.close()

    # run clean data
    for name in ('normal', 'split/new', 'split/old'):
        # skip if not split/new or split/old
        if name in names:
            proc_clean(symbol, name)
            proc_valid_clean(symbol)
            proc_fillna(symbol, name)

    # merge final
    merge_final(symbol)

    click.pause()


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of stock data.')
@click.option('--name', prompt='Name', help='(normal, others, split/old, split/new)')
def write_weekday(symbol, name):
    write_weekday_cli(symbol, name)


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of stock data.')
@click.option('--insert', prompt='Insert', help='Import weekday data')
def calc_iv(symbol, insert):
    if int(insert):
        import_weekday_cli(symbol)
    calc = DayIVCalc(symbol)
    calc.start()


if __name__ == '__main__':
    # sleep(10)
    manage()
