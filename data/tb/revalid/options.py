import os

import numpy as np
import pandas as pd

from data.models import Underlying
from rivers.settings import CLEAN_DIR

output = '%-6s | %-30s'
names = ['normal', 'others', 'split0', 'split1']
keys = ['normal', 'others', 'split/old', 'split/new']


def check_round(data):
    """
    Check options bid/ask decimal place usage
    :param data: list
    :return: str
    """
    data = np.array(data)
    r10 = (data * 10) % 1
    r05 = (data * 20.0) % 1
    if np.count_nonzero(r10) == 0:
        name = '10'
    elif np.count_nonzero(r05) == 0:
        name = '05'
    else:
        name = '01'

    return name


def option_round(value, name, method='01'):
    """
    Input a bid/ask price and change into correct round
    :param value: float
    :param name: str ('ask', 'bid')
    :param method: str ('10', '05', '01')
    :return: float
    """
    result = value
    if method == '10':
        result = np.ceil(value * 10) / 10.0
    elif method == '05':
        last_digit = round(value % 0.1, 2)
        if name == 'ask':
            if 0 < last_digit <= 0.05:
                result = round(round(value, 1) + 0.05, 2)
            elif 0.05 < last_digit <= 0.09:
                result = round(value, 1)
        elif name == 'bid':
            if 0 < last_digit <= 0.05:
                result = round(value, 1)
            elif 0.05 < last_digit <= 0.09:
                result = round(round(value, 1) - 0.05, 2)
        else:
            raise ValueError('Name can only be "ask" or "bid"')

    return result


class ValidCleanOption(object):
    def __init__(self, symbol):
        self.symbol = symbol.lower()
        self.df_list = {}

        self.path = os.path.join(CLEAN_DIR, '__%s__.h5' % self.symbol)

    def get_data(self):
        """
        Get clean options data from db
        """
        print '=' * 70
        print output % ('SEED', 'get data from db')
        db = pd.HDFStore(self.path)
        for name, key in zip(names, keys):
            try:
                self.df_list[name] = db.select('option/clean/%s' % key)
                print output % ('DATA', 'df_%s length: %d' % (key, len(self.df_list['name'])))
            except KeyError:
                pass
        db.close()
        print '=' * 70

    def save_data(self):
        """
        Save valid clean data back into db
        """
        db = pd.HDFStore(self.path)
        try:
            db.remove('option/clean')
        except KeyError:
            pass

        for name, key in zip(names, keys):
            if name in self.df_list.keys():
                db.append('option/clean/%s' % key, self.df_list[name])
                print output % ('DATA', 'save into h5 df_%s: %d' % (key, len(self.df_list[name])))
        db.close()
        print '=' * 70

    def valid(self):
        """
        Valid all clean data in df_list
        """
        df_list = {}
        for key, df_temp in self.df_list.items():
            print output % ('VALID', 'start re-valid df_%s: %d' % (key, len(df_temp)))
            df_temp = self.mark_gt_ask(df_temp)
            df_temp = self.theo_zero_bid_ask(df_temp)
            df_temp = self.theo_gt_bid_ask_zero(df_temp)
            df_list[key] = df_temp

            print output % ('VALID', 'complete re-valid df_%s' % key)
            print '-' * 70

        self.df_list = df_list
        print output % ('VALID', 'data re-valid completed')
        print '=' * 70

    def start(self):
        """
        Start all validation
        """
        self.get_data()
        self.valid()
        self.save_data()

        print 'All data re-valid and saved'
        print '=' * 70

    @staticmethod
    def mark_gt_ask(df):
        """
        Mark (minimum price or middle price) is greater than ask price
        :param df: pd.DataFrame
        :return: pd.DataFrame
        """
        df_error = df.query('mark > ask')
        # print df_error.to_string(line_width=1000)
        print output % ('ERROR', 'mark > ask: %d' % len(df_error))

        if len(df_error):
            df = df.query('mark <= ask')
            print output % ('DATA', 'after remove length: %d' % len(df))

        print '-' * 70

        return df

    @staticmethod
    def theo_zero_bid_ask(df):
        """
        When theory price is 0 and bid ask also 0
        it consider not a invalid price
        update ask into 0.01 also consider as valid
        :param df: pd.DataFrame
        :return:
        """
        df_error = df.query('theo_price == 0 & bid == ask == 0')
        print output % ('ERROR', 'theo_price == bid == ask == 0: %d' % len(df_error))

        if len(df_error):
            df = df.copy()
            df.loc[df.index.isin(df_error.index), 'ask'] = 0.01
            print output % ('DATA', 'after update length: %d' % len(df))

        print '-' * 70

        return df

    @staticmethod
    def theo_gt_bid_ask_zero(df):
        """
        When theory price greater than 0 and
        bid ask also 0 it consider a invalid price
        :param df: pd.DataFrame
        :return:
        """
        df_error = df.query('theo_price > 0 & bid == ask == 0')
        # print df_error.to_string(line_width=1000)
        print output % ('ERROR', 'theo_price > 0 & bid == ask == 0: %d' % len(df_error))

        if len(df_error):
            df = df[~df.index.isin(df_error.index)]
            print output % ('DATA', 'after update length: %d' % len(df))

        print '-' * 70

        return df

    def update_underlying(self):
        """
        Update underlying after completed
        """
        lines = []
        for name, key in zip(names, keys):
            if name in self.df_list.keys():
                lines.append('Re-valid df_%s: %d' % (key, len(self.df_list[name])))

        Underlying.write_log(self.symbol, lines)
