import datetime
import os

import pandas as pd
from django.utils.deconstruct import deconstructible
from pandas.tseries.offsets import BDay


def remove_comma(line):
    """
    Replace comma inside str line
    :param line: str
    :return: str
    """
    if '"' in line:
        values = line.split('"')
        for k, i in enumerate(values):
            if k % 2 and ',' in i:
                values[k] = i.replace(',', '')

        line = ''.join(values)
    return line


def remove_bracket(line):
    """
    Remove brackets on first item of a list
    :param line: str
    :return: str
    """
    return line.replace('(', '').replace(')', '')


def make_dict(key, values):
    """
    Make a dict join together key and values
    :param key: list
    :param values: list
    :return: dict
    """
    return {k: v for k, v in zip(key, values)}


def ts(df):
    """
    Output dataframe
    :param df: pd.DataFrame
    """
    print df.to_string(line_width=1000)


def latest_season():
    """
    Return the latest season
    :return: pd.datetime
    """
    m = int(pd.datetime.today().month) - 1
    date = pd.Timestamp('%s%02d%02d' % (
        pd.datetime.today().year,
        (m - (m % 3) + 1),
        1
    )) - BDay(1)
    return date


def ds(d):
    """
    return datetime in date format
    :param d: datetime
    :return: str
    """
    return d.strftime('%Y-%m-%d')


@deconstructible
class UploadRenameImage(object):
    def __init__(self, path):
        self.sub_path = path

    def __call__(self, instance, filename):
        symbol, ext = filename.split('.')
        symbol = symbol.replace(' ', '_')
        # set filename as random string
        filename = '{}_{}.{}'.format(
            symbol.upper(), datetime.date.today().strftime('%Y%m%d'), ext
        )

        # return the whole path to the file
        return os.path.join(self.sub_path, filename)
