import calendar
import logging
import os
import re
import numpy as np
import pandas as pd
from fractions import Fraction
from django.db.models import Q
from numba import jit

from base.ufunc import ts
from data.tb.thinkback import ThinkBack
from data.models import SplitHistory, Underlying
from rivers.settings import CLEAN_DIR, THINKBACK_DIR

# constant for get_dte_date
logger = logging.getLogger('views')
output = '%-6s | %-30s %s'
calendar.setfirstweekday(calendar.SUNDAY)
month_abbr = [calendar.month_abbr[i].upper() for i in range(1, 13)]
months = {
    '%d-%d' % (y, m): calendar.monthcalendar(y, m) for m in range(1, 13) for y in range(8, 20)
}
COLUMNS = [
    'ask', 'bid', 'date', 'delta', 'dte', 'ex_date', 'extrinsic', 'gamma', 'impl_vol',
    'index', 'index2', 'intrinsic', 'last', 'mark', 'name', 'open_int', 'option_code',
    'others', 'prob_itm', 'prob_otm', 'prob_touch', 'right', 'special', 'strike',
    'theo_price', 'theta', 'vega', 'volume'
]
BONUS_SHARE = re.compile('^([A-Za-z])\w+ \d+')


def get_dte_date2(ex_month, ex_year):
    """
    Use option contract ex_month and ex_year to get dte date
    :param ex_month: str
    :param ex_year: int
    :return: str
    """
    year = int(ex_year)
    if len(ex_month) == 4:
        # not 3th week
        month = month_abbr.index(ex_month[:3]) + 1
        week = int(ex_month[3:])
    else:
        # standard 3th week
        month = month_abbr.index(ex_month[:3]) + 1
        week = 3

    # every week need trading day as whole
    c = months['%d-%d' % (ex_year, month)]
    for w in c:
        if not any(w[1:6]):
            del c[c.index(w)]

    # get day in calendar
    day = c[week - 1][-2]
    if day == 0:
        day = [d for d in c[week - 1] if d != 0][-1]

    return '%02d%02d%02d' % (year, month, day)


def make_code2(symbol, others, right, special, ex_date, name, strike, extra=''):
    """
    Make new option code using contract data
    :return:
    :param symbol: str
    :param others: str
    :param right: str
    :param special: str
    :param ex_date: pd.datetime64
    :param name: str
    :param strike: str
    :param extra: str
    :return: str
    """
    if extra == '':
        if special == 'Mini':
            extra = 7
        elif '; US$' in others:
            extra = 2
        elif 'US$' in others:
            extra = 1
        elif BONUS_SHARE.search(others) is not None:
            extra = 1
        elif '/' in right:
            extra = 1

    strike = str(strike)
    if strike[-2:] == '.0':
        strike = strike.replace('.0', '')

    new_code = '{symbol}{extra}{year}{month}{day}{name}{strike}'.format(
        symbol=symbol.upper(),
        extra=extra,
        year=ex_date.date().strftime('%y'),
        month=ex_date.date().strftime('%m'),
        day=ex_date.date().strftime('%d'),
        name=name[0].upper(),
        strike=strike
    )

    return new_code


def change_code(symbol, code, others, right, special):
    """
    Make new option code using contract data
    :param symbol: str
    :param code: str
    :param others: str
    :param right: str
    :param special: str
    :return: str
    """
    extra = ''
    if special == 'Mini':
        extra = 7
    elif '; US$' in others:
        extra = 2
    elif 'US$' in others:
        extra = 1
    elif BONUS_SHARE.search(others) is not None:
        extra = 1
    elif '/' in right:
        extra = 1

    wrong = re.search('^([A-Z]+)\d+[CP]+\d+', code).group(1)

    new_code = '{symbol}{extra}{right}'.format(
        symbol=symbol.upper(), extra=extra, right=code[len(wrong):]
    )

    return new_code


def check_code(symbol, contract):
    """
    Check option_code is valid
    no old code format and cannot without symbol
    :param symbol: str
    :param contract: Series
    :return: str
    """
    if len(contract['option_code']) < 9:  # old format or no symbol
        # ex_date = pd.Timestamp(get_dte_date2(contract['ex_month'], int(contract['ex_year'])))
        try:
            ex_date = contract['ex_date']
        except KeyError:
            print contract
            print symbol
            raise KeyError('Invalid ex_date: %s, %s' % (symbol, contract))

        new_code = make_code2(
            symbol, contract['others'], contract['right'], contract['special'],
            ex_date, contract['name'], contract['strike']
        )
        print output % ('CODE', 'Update (old format): %-16s -> %-16s' % (
            contract['option_code'], new_code
        ), '')
    elif contract['option_code'][:len(symbol)] != symbol.upper():
        # some ex_date is on thursday because holiday or special date
        new_code = change_code(
            symbol, contract['option_code'], contract['others'], contract['right'], contract['special']
        )
        print output % ('CODE', 'Update (no symbol):  %-16s -> %-16s' % (
            contract['option_code'], new_code
        ), '')
    else:
        new_code = contract['option_code']

    return new_code


def split_code(code, strike):
    symbol = re.search('^([A-Z]+)\d+[CP]+\d+', code).group(1)
    ex_date = re.search('^[A-Z]+(\d+)[CP]+\d+', code).group(1)
    name = re.search('^[A-Z]+\d+([CP]+)\d+', code).group(1)
    strike = int(strike) if int(strike) == strike else strike

    return '{symbol}{extra}{ex_date}{name}{strike}'.format(
        symbol=symbol, extra=1, ex_date=ex_date, name=name, strike=strike
    )


def get_contract(df_current):
    """
    Get contract data from first row of DataFrame
    :param df_current: pd.DataFrame
    :return: Series
    """
    return df_current.iloc[0][[
        'ex_date', 'name', 'option_code', 'others', 'right', 'special', 'strike'
    ]]


class RawOption(object):
    def __init__(self, symbol, df_stock):
        """
        :param symbol: str
        :param df_stock: pd.DataFrame
        """
        self.symbol = symbol
        self.df_stock = df_stock.sort_index(ascending=False)

        self.df_all = pd.DataFrame()

        # raw data
        self.df_normal = pd.DataFrame()
        self.df_split0 = pd.DataFrame()
        self.df_others0 = pd.DataFrame()

        # final data, old format
        self.df_split1 = pd.DataFrame()
        self.df_others1 = pd.DataFrame()

        # final data, new format
        self.df_split2 = pd.DataFrame()

        self.db_path = os.path.join(CLEAN_DIR, '__%s__.h5' % self.symbol.lower())

    def get_data(self):
        """
        Get data from thinkback file and make df_all
        """
        print '=' * 70
        print output % ('GET', 'Option data:', self.symbol.upper())
        print '=' * 70

        db = pd.HDFStore(self.db_path)
        try:
            df_all = db['all']
        except KeyError:
            df_all = pd.DataFrame()
        db.close()

        if len(df_all):
            self.df_all = df_all.copy()
            logger.info('Get data from clean: %s' % self.db_path)
            print output % ('SKIP', 'Read from clean, df_all: %d' % len(df_all), '')
        else:
            symbol0 = self.symbol.lower()
            symbol1 = self.symbol.upper()

            options = []
            path = os.path.join(THINKBACK_DIR, symbol0)
            logger.info('Get data from path: %s' % path)
            for key in np.arange(len(self.df_stock)):
                # open path get option data
                date = self.df_stock.index[key].date().strftime('%Y-%m-%d')
                fpath = os.path.join(
                    path, date[:4], '%s-StockAndOptionQuoteFor%s.csv' % (date, symbol1)
                )
                print output % (key, 'Read %s' % os.path.basename(fpath), '')
                # _, data = ThinkBack(fpath).read()
                options += ThinkBack(fpath).get_options()

            # make all options df
            df_all = pd.DataFrame(options)
            # df_all['date'] = pd.to_datetime(df_all['date'])
            # df_all['ex_date'] = pd.to_datetime(df_all['ex_date'])

            self.df_all = df_all

            db = pd.HDFStore(self.db_path)
            db['all'] = df_all
            db.close()

    def group_data(self):
        """
        Group data base on normal, split or others
        """
        print '=' * 70
        print output % ('GROUP', 'Raw data: normal, split, others', '')
        print '=' * 70

        df_all = self.df_all.copy()
        """:type: pd.DataFrame"""

        df_others = df_all[df_all['others'] != ""]
        df_all = df_all[~df_all.index.isin(df_others.index)]
        # df_split = df_all.query('right != "100" & special != "Mini"')
        df_split = df_all[df_all['right'].apply(lambda r: '/' in r)]
        df_all = df_all[~df_all.index.isin(df_split.index)]

        self.df_normal = df_all
        self.df_split0 = df_split
        self.df_others0 = df_others

    def get_old_split_data(self):
        """
        Split is always merge with normal data
        because old data is always normal
        but others can be split then become others
        """
        print '=' * 70
        print output % ('MERGE', 'Old split data, length:', len(self.df_split0))

        if len(self.df_split0):
            data = []
            indexes = np.array(self.df_split0['index'].unique())
            for j in np.arange(len(indexes)):
                index = indexes[j]
                print output % ('SPLIT', 'Get row data for split', 'index: %s' % index)
                df_current = self.df_split0.query('index == %r' % index).copy()
                """:type: pd.DataFrame"""
                # print df_current.to_string(line_width=1000)

                if len(df_current) != len(df_current['date'].unique()):
                    # if too many split, use new raw2 options

                    print output % ('ERROR', 'Duplicated row problem', '')
                    date_counts = df_current['date'].value_counts()
                    dup_dates = list(date_counts[date_counts == 2].index)
                    df_dup = df_current[df_current['date'].isin(dup_dates)]
                    df_group = df_dup.group_data('date')

                    dup_counts = 0
                    for n in np.arange(len(dup_dates)):
                        dup_date = dup_dates[n]
                        dup_row = df_group.get_group(dup_date)
                        # print dup_row.to_string(line_width=1000)
                        if len(dup_row['ask'].unique()) == 1:
                            dup_counts += 1

                    if dup_counts == len(dup_dates):
                        print output % ('EXPORT', 'Duplicated row data', index)
                        # remove duplicated in df_current
                        old_length = len(df_current)
                        df_current = df_current[~df_current['date'].duplicated()]
                        print output % ('DATA', 'df_current old: %d, new: %d' % (
                            old_length, len(df_current)
                        ), '')
                    else:
                        # print 'found not same'
                        raise LookupError('Split data got duplicate date')

                print output % ('REMOVE', 'old data in df_split removed', '')
                self.df_split0 = self.df_split0[~self.df_split0.index.isin(df_current.index)]

                # update option_code
                contract = get_contract(df_current)
                new_code = check_code(self.symbol, contract)
                df_current['option_code'] = new_code
                print output % ('CODE', 'using option_code:', new_code)

                # print df_current.to_string(line_width=1000)
                data.append(df_current)
                print '-' * 70

            print output % ('MERGE', 'Completed, length:', len(self.df_split0))

            df_split = pd.concat(data)
            """:type: pd.DataFrame"""
            df_split = df_split.sort_values('date', ascending=False)

            self.df_split1 = df_split
        print '=' * 70

    def get_others_data(self):
        """
        Others is always old format, new format got no others or right
        """
        print '=' * 70
        print output % ('MERGE', 'Old others data, length:', len(self.df_others0))
        print '=' * 70

        # codes = df_others['option_code'].unique()
        # df_others = df_others[df_others['index'] == 'JAN11PUT2.5']
        # print df_others.to_string(line_width=1000)
        # print df_normal[df_normal['index'] == 'JAN11PUT2.5'].to_string(line_width=1000)

        if len(self.df_others0):
            group = self.df_others0.group_data('index2')
            dates = pd.Series(group['date'].max()).sort_values(ascending=False)
            # print dates

            data = []
            for j in np.arange(len(dates)):
                index2 = dates.index[j]
                date = dates[index2]
                print output % ('INDEX2', index2, '')
                print output % ('DATE', date.strftime('%Y-%m-%d'), '')
                df_current = self.df_others0.query('index2 == %r & date == %r' % (index2, date))

                if len(df_current) == 0:
                    print output % ('EMPTY', 'No more others data (added)', '')
                    print '-' * 70
                    continue

                df_current = self.df_others0.query('option_code == %r | index2 == %r' % (
                    df_current['option_code'].iloc[0], index2
                ))

                index = df_current['index'].iloc[0]
                code = df_current['option_code'].iloc[0]
                right = df_current['right'].iloc[0]

                print output % ('OTHERS', 'Get others all continue rows', len(df_current))
                # print df_current.to_string(line_width=1000)

                # print df_start.to_string(line_width=1000)
                df_continue = self.df_others0.query('index == %r & date < %r' % (
                    df_current['index'].iloc[0], df_current['date'].iloc[-1]
                ))
                while len(df_continue):
                    # check duplicate
                    if len(df_continue) != len(df_continue['date'].unique()):
                        print output % ('OTHERS', 'Duplicate date in continue data', '')
                        for key, value in [('option_code', code), ('right', right)]:
                            df_similar = df_continue[df_continue[key] == value]

                            if len(df_similar):
                                print output % ('OTHERS', 'Found others continue data:',
                                                '%s: %s' % (key, value))
                                df_current = pd.concat([df_current, df_similar])
                                self.df_others0 = self.df_others0[~self.df_others0.index.isin(df_similar.index)]
                                break
                        else:
                            # no break, loop until end
                            print output % ('OTHERS', 'Found data but duplicate date', '')
                            df_continue = pd.DataFrame(columns=['index', 'date'])
                    else:
                        print output % ('OTHERS', 'Merge others continue data', len(df_continue))
                        df_current = pd.concat([df_current, df_continue])
                        self.df_others0 = self.df_others0[~self.df_others0.index.isin(df_continue.index)]

                    oldest = df_current['date'].iloc[-1]
                    df_continue = df_continue.query('index == %r & date < %r' % (index, oldest))
                    # print df_current.to_string(line_width=1000)
                else:
                    # remove data in df_others
                    print output % ('REMOVE', 'Added others continue data', 'old data removed')
                    self.df_others0 = self.df_others0[~self.df_others0.index.isin(df_current.index)]

                # use previous check
                df_current = pd.concat([df_current, df_continue])
                """:type: pd.DataFrame"""

                # normal will be add later on another method
                if len(df_current) != len(df_current['date'].unique()):
                    print output % ('ERROR', 'Duplicated row problem', '')
                    date_counts = df_current['date'].value_counts()
                    dup_dates = list(date_counts[date_counts == 2].index)
                    df_dup = df_current[df_current['date'].isin(dup_dates)]
                    df_group = df_dup.group_data('date')

                    dup_counts = 0
                    for n in np.arange(len(dup_dates)):
                        dup_date = dup_dates[n]
                        dup_row = df_group.get_group(dup_date)
                        # print dup_row.to_string(line_width=1000)
                        if len(dup_row['ask'].unique()) == 1:
                            dup_counts += 1

                    if dup_counts == len(dup_dates):
                        print output % ('EXPORT', 'Duplicated row data', index)
                        # remove duplicated in df_current
                        old_length = len(df_current)
                        df_current = df_current[~df_current['date'].duplicated()]
                        print output % ('DATA', 'df_current old: %d, new: %d' % (
                            old_length, len(df_current)
                        ), '')
                    else:
                        print df_current.to_string(line_width=1000)
                        raise LookupError('Duplicate date for others!!!')

                # update code
                contract = get_contract(df_current)
                new_code = check_code(self.symbol, contract)
                df_current['option_code'] = new_code
                print output % ('CODE', 'using option_code:', new_code)

                # done, append into data
                data.append(df_current)
                print '-' * 70
                # print df_current.to_string(line_width=1000)

            print output % ('MERGE', 'Completed, length:', len(self.df_others0))

            df_others = pd.concat(data)
            """:type: pd.DataFrame"""
            df_others = df_others.sort_values('date', ascending=False)

            self.df_others1 = df_others

        print '=' * 70

    def continue_split_others(self):
        """
        Run both others and split continue normal using date descending
        speed up version...
        """
        print '=' * 70
        print output % ('JOIN', 'Old format split/others data', '')
        print '=' * 70

        print output % ('STAT', 'df_normal length: %d' % len(self.df_normal), '')
        print output % ('STAT', 'df_split1 length: %d' % len(self.df_split1), '')
        print output % ('STAT', 'df_others1 length: %d' % len(self.df_others1), '')
        print '-' * 70

        if len(self.df_split1) == 0 and len(self.df_others1) == 0:
            print output % ('INFO', 'No data for continue split/others', '')
            return None

        df_date0 = pd.DataFrame()
        group0 = None
        if len(self.df_split1):
            group0 = self.df_split1.group_data('option_code')
            dates0 = group0['date'].min()
            df_date0 = pd.DataFrame(dates0)
            df_date0['event'] = 'split'

        df_date1 = pd.DataFrame()
        group1 = None
        if len(self.df_others1):
            group1 = self.df_others1.group_data('option_code')
            dates1 = group1['date'].min()
            df_date1 = pd.DataFrame(dates1)
            df_date1['event'] = 'others'

        df_date = pd.concat([df_date0, df_date1])
        """:type: pd.DataFrame"""
        dates = df_date.sort_values('date')

        # new normal group
        group2 = self.df_normal.groupby('index')
        used_index = []
        remain_data = {}
        append_id = []

        # more in list
        split_data = []  # cause memory error, goog
        others_data = []
        split_panel = []
        others_panel = []

        for j in np.arange(len(dates)):
            code = dates.index[j]
            row = dates.ix[code]

            try:
                print output % (
                    'FOR', 'code: %s date: %s' % (code, row['date'].strftime('%Y-%m-%d')),
                    'Event: %s' % row['event']
                )
            except AttributeError:
                dup_code = row.index[0]
                df_split2 = group0.get_group(dup_code).copy()
                df_others2 = group1.get_group(dup_code).copy()

                ts(df_others2)
                ts(df_split2)


                raise


            # get df_current
            if row['event'] == 'split':
                df_current = group0.get_group(code).copy()
            elif row['event'] == 'others':
                df_current = group1.get_group(code).copy()
            else:
                raise LookupError('Invalid event name: %s' % row['event'])

            print output % (row['event'].upper(), 'Total length:', len(df_current))

            index = df_current.loc[df_current['date'] == row['date'], 'index'].iloc[0]

            print output % ('NORMAL', 'Get normal row using', 'index: %s' % index)
            oldest = row['date']

            # get df_continue
            if index in remain_data.keys():
                df_continue0 = remain_data[index]
                df_continue = df_continue0[df_continue0['date'] < oldest].copy()
                remain_data[index] = df_continue0[df_continue0['date'] >= oldest]  # can empty
            elif index in used_index:
                df_continue = pd.DataFrame(columns=COLUMNS)  # no column result error
            else:
                try:
                    df_continue0 = group2.get_group(index)
                    df_continue = df_continue0[df_continue0['date'] < oldest].copy()

                    if len(df_continue) == len(df_continue0):
                        used_index.append(index)
                    else:
                        remain_data[index] = df_continue0[df_continue0['date'] >= oldest]
                except KeyError:
                    df_continue = pd.DataFrame(columns=COLUMNS)  # no column result error
                    print output % ('EMPTY', 'No continue data found in df_normal', '')

            if len(df_continue):
                if len(df_continue) == len(df_continue['date'].unique()):
                    append_id += list(df_continue.index)
                else:
                    print output % ('NORMAL', 'Found normal but duplicate date', len(df_continue))

            # update option_code
            df_current['option_code'] = df_current['option_code'].iloc[0]
            df_continue['option_code'] = df_current['option_code'].iloc[0]  # remove concat
            print output % ('CODE', 'using option_code:', df_current['option_code'].iloc[0])

            # add into data
            if row['event'] == 'split':
                split_data += [df_current, df_continue]

                if len(split_data) > 99:  # remove memory error
                    print output % ('JOIN', 'concat 100 split_data', 'remove memory error')
                    print '-' * 70
                    df_split = pd.concat(split_data)
                    split_panel.append(df_split)
                    split_data = []

            else:
                others_data += [df_current, df_continue]

                if len(others_data) > 99:  # remove memory error
                    print output % ('JOIN', 'concat 100 others_data', 'remove memory error')
                    print '-' * 70
                    df_others = pd.concat(others_data)
                    others_panel.append(df_others)
                    others_data = []

            print '-' * 70
        else:
            # add remain split/others data
            if len(split_data):
                df_split = pd.concat(split_data)
                split_panel.append(df_split)

            if len(others_data):
                df_others = pd.concat(others_data)
                others_panel.append(df_others)

        # save back into df
        if len(split_data):
            df_split1 = pd.concat(split_panel)
            """:type: pd.DataFrame"""
            df_split1 = df_split1.sort_values('date', ascending=False)
            self.df_split1 = df_split1

        if len(others_data):
            df_others1 = pd.concat(others_panel)
            """:type: pd.DataFrame"""
            df_others1 = df_others1.sort_values('date', ascending=False)
            self.df_others1 = df_others1

        # remove id in normal
        self.df_normal.drop(append_id)

        print 'df_split0 length: %d' % len(self.df_split0)
        print 'df_others0 length: %d' % len(self.df_others0)
        print 'df_normal length: %d' % len(self.df_normal)
        print 'df_split1 length: %d' % len(self.df_split1)
        print 'df_others1 length: %d' % len(self.df_others1)

    def merge_new_split_data(self):
        """
        After 2013 most of the option_code direct change strike
        when split or special dividend happen
        for example: 50 and split 1 for 2 will become 100
        for example: special dividend $2, 50 strike will normal cost 5 will become 3
        """
        print '=' * 70
        print output % ('MERGE', 'New split data', '')
        print '=' * 70
        print output % ('DATA', 'df_normal length:', len(self.df_normal))

        split_history = SplitHistory.objects.filter(
            Q(symbol=self.symbol.upper()) & Q(date__gte='2013-01-01')
        )
        """:type: pd.DataFrame"""
        print output % ('SPLIT', 'Split history in db: %d' % len(split_history), split_history)
        print '-' * 70

        # print df_normal.head().to_string(line_width=1000)
        start, stop = self.df_normal['date'].min(), self.df_normal['date'].max()

        exists = {
            'found': 0,
            'not': 0
        }
        data = []
        for split in split_history:
            split_date = pd.to_datetime(split.date)
            if not (start < split_date < stop):
                continue

            print output % ('SPLIT', 'New format direct change strike', split)

            df_before = self.df_normal[self.df_normal['date'] < split_date].copy()
            df_after = self.df_normal[self.df_normal['date'] >= split_date].copy()
            df_before['expire'] = df_before['ex_date'] < split_date
            df_before = df_before[~df_before['expire']]
            # skip no bid ask
            df_before = df_before.query('bid > 0 | ask > 0')

            for code in df_before['option_code'].unique():
                df0 = df_before.query('option_code == %r' % code)
                print output % ('SPLIT', 'New split %s' % code, 'total: %d' % len(df0))
                # print df_code.to_string(line_width=1000)
                c = get_contract(df0)

                old_code = c['option_code']
                new_strike = round(c['strike'] * Fraction(split.fraction), 2)

                new_code = split_code(old_code, new_strike)

                print output % (
                    'CODE', 'Strike change after split', '%s -> %s' % (old_code, new_code)
                )

                df1 = df_after[df_after['option_code'] == new_code]
                if len(df1):
                    exists['found'] += 1
                    print output % ('SPLIT', 'new option_code found', exists)

                    df_new = pd.concat([df0, df1])
                    """:type: pd.DataFrame"""
                    df_new = df_new.sort_values('date', ascending=False)
                    df_new['new_code'] = df_new['option_code'].iloc[0]

                    print output % ('SEARCH', 'New option_code data FOUND', 'total: %d' % len(df1))
                    print output % ('MERGE', 'Merge new split', 'total: %d' % len(df_new))

                    data.append(df_new)
                    # print df_new.to_string(line_width=1000)
                else:
                    exists['not'] += 1
                    print output % ('SEARCH', 'New option_code NOT FOUND', exists)

                print '-' * 70

        if len(data):
            print output % ('DONE', 'All split data is merge', 'total code: %d' % len(data))
            # merge df_split
            df_split = pd.concat(data)
            """:type: pd.DataFrame"""

            del df_split['expire']
            self.df_split2 = df_split

            self.df_normal = self.df_normal[~self.df_normal.index.isin(df_split.index)]
            print output % ('REMOVE', 'old data in df_normal removed', '')
            print output % ('DATA', 'df_normal length:', len(self.df_normal))
        else:
            print output % ('EMPTY', 'No new split data for', self.symbol)

    def format_normal_code(self):
        """
        Format option code for DataFrame
        """
        print output % ('CODE', 'start format option_code', '')
        print '=' * 70

        if not len(self.df_normal):
            return

        # print df.head().to_string(line_width=1000)
        df_format = self.df_normal.sort_values('date', ascending=False).copy()

        # multi option_code
        group = df_format.group_data('index2')
        unique = group['option_code'].unique()
        unique = unique[unique.apply(lambda x: len(x) > 1)]
        df_unique = df_format[df_format['index2'].isin(unique.index)]
        df_format = df_format[~df_format['index2'].isin(unique.index)]

        data = []
        for index in unique.index:
            df_current = df_unique.query('%s == %r' % ('index2', index)).copy()
            contract = get_contract(df_current)
            new_code = check_code(self.symbol, contract)

            df_current['option_code'] = new_code
            data.append(df_current.copy())

            print output % ('CODE', 'Set unique code:     %s' % new_code, '')

        # option_code too_short and no symbol
        codes = pd.Series(df_format['option_code'].unique())

        date_length = 6
        type_length = 1
        strike_length = 1
        min_length = len(self.symbol) + date_length + type_length + strike_length
        old_codes0 = codes[codes.apply(lambda c: len(c) < min_length)]
        symbol = self.symbol.upper()
        old_codes1 = codes[codes.apply(lambda c: symbol not in c)]
        error_codes = pd.concat([old_codes0, old_codes1])
        """:type: pd.Series"""
        error_codes = error_codes.drop_duplicates()
        df_old = df_format[df_format['option_code'].isin(error_codes)]
        df_format = df_format[~df_format['option_code'].isin(error_codes)]

        for old_code in error_codes:
            df_current = df_old.query('option_code == %r' % old_code).copy()
            contract = get_contract(df_current)
            new_code = check_code(self.symbol, contract)

            df_current['option_code'] = new_code
            data.append(df_current.copy())

            print output % ('CODE', 'Update old code:      %s' % new_code, '')

        if len(data):
            df_update = pd.concat(data)
            """:type: pd.DataFrame"""

            df_format = pd.concat([df_format, df_update])
            """:type: pd.DataFrame"""

            # assert len(df_format) == len(df)
            print output % ('STAT', 'Old length: %d, Format length: %d' % (
                len(self.df_normal), len(df_format)
            ), '')

            self.df_normal = df_format
            """:type: pd.DataFrame"""

        print '=' * 70

    def start(self, path=''):
        """
        Start extract all option from raw csv data
        :param path: str
        """
        # main functions
        logger.info('Get data from thinkback folder')
        self.get_data()
        logger.info('Group data into df_normal, df_split, df_others')
        self.group_data()
        logger.info('Get df_old_split data')
        self.get_old_split_data()
        logger.info('Get df_others data')
        self.get_others_data()
        logger.info('Continue df_old_split and df_others data')
        self.continue_split_others()
        logger.info('Get and continue df_new_split data')
        self.merge_new_split_data()
        logger.info('Format option code')
        self.format_normal_code()

        # re_index, drop column
        logger.info('Format data columns')
        df_list = [self.df_normal, self.df_others1, self.df_split1, self.df_split2]
        for df in df_list:
            df.reset_index(drop=True, inplace=True)
            try:
                df.drop(['index', 'index2'], axis=1, inplace=True)
            except ValueError:
                pass

        print '=' * 70
        print output % ('IMPORT', 'Complete extract option data', '')
        print '=' * 70
        print output % ('STAT', 'df_normal length: %d' % len(self.df_normal), '')
        print output % ('STAT', 'df_others length: %d' % len(self.df_others1), '')
        print output % ('STAT', 'df_split1 length: %d' % len(self.df_split1), '')
        print output % ('STAT', 'df_split2 length: %d' % len(self.df_split2), '')

        if path != '':
            self.db_path = path

        logger.info('Save data into clean, path: %s' % path)
        db = pd.HDFStore(self.db_path)
        try:
            db.remove('option/raw')
        except KeyError:
            pass
        db.append('option/raw/normal', self.df_normal)
        db.append('option/raw/others', self.df_others1)
        db.append('option/raw/split/old', self.df_split1)
        db.append('option/raw/split/new', self.df_split2)
        db.close()

        print output % ('SAVE', 'All data saved', '')
        logger.info('Complete save raw options')

    def update_underlying(self):
        """
        Update underlying after completed
        """
        Underlying.write_log(self.symbol, [
            'Raw df_normal length: %d' % len(self.df_normal),
            'Raw df_others length: %d' % len(self.df_others1),
            'Raw df_split/old length: %d' % len(self.df_split1),
            'Raw df_split/new length: %d' % len(self.df_split2)
        ])
