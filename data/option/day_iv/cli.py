import click
import pandas as pd
import time
import os
from data.models import SplitHistory
from data.tb.valid.options import ValidRawOption
from data.tb.clean import CleanNormal
from datetime import timedelta
from fractions import Fraction
from subprocess import PIPE
from subprocess import Popen
from data.tb.raw.options import ExtractOption
from data.tb.clean.split_old import CleanSplitOld
from data.tb.final.views import change_right
from rivers.settings import QUOTE, CLEAN


def write_weekday_cli(symbol, name):
    if name == 'normal':
        clean_option = CleanNormal(symbol)

        df_div, df_rate, df_stock = clean_option.get_quote_data()
        db = pd.HDFStore(CLEAN)
        df_normal = db.select('iv/%s/valid/normal' % symbol.lower())
        df_normal = df_normal.reset_index(drop=True)
        db.close()
        clean_option.merge_option_data(df_normal, df_div, df_rate, df_stock)

        lines = clean_option.to_csv().split()
    elif name == 'split/old':
        clean_option = CleanSplitOld(symbol)
        df_div, df_rate, df_stock = clean_option.get_quote_data()

        db = pd.HDFStore(CLEAN)
        df_split0 = db.select('iv/%s/valid/split/old' % symbol.lower())
        df_split0 = df_split0.reset_index(drop=True)
        db.close()
        clean_option.merge_option_data(df_split0, df_div, df_rate, df_stock)

        clean_option.update_split_date()
        lines = clean_option.to_csv().split()
    else:
        raise KeyError('No DataFrame for "%s"' % name)

    for line in lines:
        click.echo(line)


def import_weekday_cli(symbol):
    """
    :param symbol: str
    """
    click.echo('Create raw data for: %s' % symbol.upper())
    db = pd.HDFStore(QUOTE)
    df_stock = db.select('stock/thinkback/%s' % symbol.lower())
    db.close()

    # df_stock = df_stock.ix['2009-07-01':'2009-12-31']

    # run import raw option
    extract_option = ExtractOption(symbol, df_stock)
    extract_option.get_data()
    extract_option.group_data()

    # missing split here
    df_normal = extract_option.df_normal
    df_split0 = extract_option.df_split0
    split_history = SplitHistory.objects.filter(symbol=symbol.upper())

    for split in split_history:
        df = df_normal.query(
            'date == %r & special != "Mini"' % pd.to_datetime(split.date)
        )
        rights = df['right'].unique()
        if len(rights) < 2:
            df_normal.loc[
                df_normal.index.isin(df.index), 'strike'
            ] /= float(Fraction(split.fraction))

            df_normal.loc[
                df_normal.index.isin(df.index), 'right'
            ] = str(Fraction(split.fraction) * 100)

    # run valid raw option
    valid_option = ValidRawOption(symbol)
    valid_option.df_list['normal'] = df_normal
    valid_option.df_list['split1'] = df_split0
    df_result = valid_option.valid()

    # save into db
    db = pd.HDFStore(CLEAN)
    try:
        db.remove('iv/%s/valid' % symbol.lower())
    except KeyError:
        pass
    db.append('iv/%s/valid/normal' % symbol.lower(), df_result['normal'])
    if len(df_result['split0']):
        db.append('iv/%s/valid/split/old' % symbol.lower(), df_result['split0'])
    db.close()

    for name in ('normal', 'split/old'):
        if name == 'split/old' and len(df_result['split0']) == 0:
            continue

        click.echo('Clean %s data for: %s' % (name, symbol.upper()))
        path = os.getcwd().replace('\\', '/')
        cmd = r'{writer} | {reader}'.format(
            writer=r'python "{path}/data/manage.py" write_weekday'
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
            clean_option.df_all = df_result['normal']
        elif name == 'split/old':
            clean_option = CleanSplitOld(symbol)
            clean_option.df_all = df_result['split0']
        else:
            raise KeyError('No DataFrame for "%s"' % name)

        df_clean = clean_option.convert_data(lines)

        if name == 'split/old':
            df_clean['strike'] = df_clean.apply(
                lambda x: x['strike'] / float(Fraction(x['right'])),
                axis=1
            )
            df_clean['right'] = df_clean['right'].apply(change_right)

        # save data
        db = pd.HDFStore(CLEAN)
        try:
            db.remove('iv/%s/valid/%s' % (symbol.lower(), name))
            db.remove('iv/%s/clean/%s' % (symbol.lower(), name))
        except KeyError:
            pass
        db.append('iv/%s/clean/%s' % (symbol.lower(), name), df_clean)
        db.close()

        print 'iv df_%s: %d' % (name, len(df_clean))

    click.pause()


