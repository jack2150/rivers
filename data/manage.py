import os
import sys

from data.tb.fillna.normal import FillNaNormal
from data.tb.fillna.split_new import FillNaSplitNew
from data.tb.fillna.split_old import FillNaSplitOld
from data.tb.final.views import merge_final

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rivers.settings")

import click
import pandas as pd
import time
from data.tb.valid.options import ValidOption
from data.tb.clean import CleanNormal
from datetime import timedelta
from subprocess import PIPE
from subprocess import Popen
from data.tb.raw.options import ExtractOption
from data.tb.raw.stocks import extract_stock
from data.tb.clean.split_new import CleanSplitNew
from data.tb.clean.split_old import CleanSplitOld
from rivers.settings import QUOTE, CLEAN


@click.group()
def manage():
    pass


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of stock data.')
def import_stock(symbol):
    click.echo('Import thinkback stock data: %s' % symbol.upper())
    extract_stock(symbol)
    click.pause()


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of raw option data.')
def prepare_raw(symbol):
    click.echo('Create raw data for: %s' % symbol.upper())
    db = pd.HDFStore(QUOTE)
    df_stock = db.select('stock/thinkback/%s' % symbol.lower())
    db.close()

    # run import raw option
    extract_option = ExtractOption(symbol, df_stock)
    extract_option.start()
    extract_option.update_underlying()

    click.pause()


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of valid raw options.')
def valid_raw(symbol):
    click.echo('Valid raw data for: %s' % symbol.upper())

    # run valid raw option
    valid_option = ValidOption(symbol)
    valid_option.start()
    valid_option.update_underlying()
    click.pause()


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

    # save data
    if name == 'normal':
        clean_option = CleanNormal(symbol)
    elif name == 'split/new':
        clean_option = CleanSplitNew(symbol)
    elif name == 'split/old':
        clean_option = CleanSplitOld(symbol)
    else:
        raise KeyError('No DataFrame for "%s"' % name)

    clean_option.get_merge_data()
    clean_option.save_clean(lines)
    clean_option.update_underlying()


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of stock data.')
@click.option('--name', prompt='Name', help='(normal, others, split/old, split/new)')
def fillna_missing(symbol, name):
    click.echo('Fill missing clean for: %s %s' % (symbol.upper(), name))

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
    click.pause()


@manage.command()
@click.option('--symbol', prompt='Symbol', help='Symbol of stock data.')
def import_option(symbol):
    click.echo('Import thinkback stock data: %s' % symbol.upper())
    extract_stock(symbol)

    click.echo('Create raw data for: %s' % symbol.upper())
    db = pd.HDFStore(QUOTE)
    df_stock = db.select('stock/thinkback/%s' % symbol.lower())
    db.close()

    # run import raw option
    extract_option = ExtractOption(symbol, df_stock)
    extract_option.start()
    extract_option.update_underlying()

    # run valid raw option
    valid_option = ValidOption(symbol)
    valid_option.start()
    valid_option.update_underlying()

    db = pd.HDFStore(CLEAN)
    df_list = {}
    for name in ('normal', 'split/new', 'split/old'):
        try:
            df_list[name] = db.select('option/%s/valid/%s' % (symbol.lower(), name))
        except KeyError:
            pass
    db.close()

    # run clean data
    path = os.getcwd().replace('\\', '/')
    for name in ('normal', 'split/new', 'split/old'):
        # skip if not split/new or split/old
        if name not in df_list.keys():
            continue

        click.echo('Clean %s data for: %s' % (name, symbol.upper()))

        cmd = r'{writer} | {reader}'.format(
            writer=r'python "{path}/data/manage.py" write_valid'
                   r' --symbol={symbol} --name={name}'.format(path=path, symbol=symbol, name=name),
            reader=r'"{path}/data/tb/clean/clean.exe"'.format(path=path)
        )

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

        # save data
        if name == 'normal':
            clean_option = CleanNormal(symbol)
        elif name == 'split/new':
            clean_option = CleanSplitNew(symbol)
        elif name == 'split/old':
            clean_option = CleanSplitOld(symbol)
        else:
            raise KeyError('No DataFrame for "%s"' % name)

        clean_option.get_merge_data()
        clean_option.save_clean(lines)
        clean_option.update_underlying()

        # fillna missing
        click.echo('Fill missing clean for: %s %s' % (symbol.upper(), name))

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

    # merge final
    merge_final(symbol)


if __name__ == '__main__':
    # sleep(10)
    manage()
