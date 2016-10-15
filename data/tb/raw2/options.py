import logging
import os
import re
from fractions import Fraction

import numpy as np
import pandas as pd
from django.db.models import Q
from pandas.tseries.offsets import BDay
from base.ufunc import ts, ds
from data.tb.thinkback import ThinkBack
from data.models import SplitHistory, Underlying
from rivers.settings import CLEAN_DIR, THINKBACK_DIR, QUOTE_DIR

logger = logging.getLogger('views')
output = '%-6s | %-30s %s'
MIN_LENGTH = len('122582C1')
BONUS_SHARE = re.compile('^([A-Za-z])\w+ \d+')
RIGHT_OTHERS = re.compile('^[A-Z]+\s\d+')
SPLIT_FORMAT0 = re.compile('^US\$\s\d+\.\d+')
SPLIT_FORMAT1 = re.compile('^US\$\s\d+')


class CodeChanger(object):
    """
    Method use for option code change and code related
    """
    @classmethod
    def code_change(cls, x, symbol, length, extra=''):
        """
        Change code when 2 condition met:
        1. old format option_code
        2. new format option_code without symbol
        :param extra:
        :param x: dict
        :param symbol: str
        :param length: int
        :return: str
        """
        if len(x['option_code']) < length:  # old format or no symbol
            new_code = cls.make_code1(
                symbol, x['others'], x['right'], x['special'],
                x['ex_date'], x['name'], x['strike'], extra
            )
            print output % ('CODE', 'Update (old format): %-16s -> %-16s' % (
                x['option_code'], new_code
            ), '')
        elif x['option_code'][:len(symbol)] != symbol.upper():
            # some ex_date is on thursday because holiday or special date
            new_code = cls.make_code1(
                symbol, x['others'], x['right'], x['special'],
                x['ex_date'], x['name'], x['strike'], extra
            )
            print output % ('CODE', 'Update (no symbol):  %-16s -> %-16s' % (
                x['option_code'], new_code
            ), '')
        else:
            new_code = x['option_code']

        return new_code

    @staticmethod
    def make_code1(symbol, others, right, special, ex_date, name, strike, extra=''):
        """
        Make new option code using contract data only
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
        elif extra == 'empty':
            extra = ''

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

    @staticmethod
    def make_code0(symbol, code, others, right, special, extra=''):
        """
        Make new option code using option_code and contract data
        :param symbol: str
        :param code: str
        :param others: str
        :param right: str
        :param special: str
        :param extra: str/int
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

        wrong = re.search('^([A-Z]+)\d+[CP]+\d+', code).group(1)

        new_code = '{symbol}{extra}{remain}'.format(
            symbol=symbol.upper(), extra=extra, remain=code[len(wrong):]
        )

        return new_code

    @staticmethod
    def got_extra(code):
        """
        Check code have extra field
        :param code: str
        :return: bool
        """
        try:
            ex_date = re.search('^[A-Z]+(\d+)[CP]+\d+', code).group(1)
            if len(ex_date) == 7:
                result = True
            else:
                result = False
        except AttributeError:
            result = True  # old format, no need

        return result

    @staticmethod
    def get_extra(code):
        """
        Get code extra
        :param code: str
        :return: bool
        """
        ex_date = re.search('^[A-Z]+(\d+)[CP]+\d+', code).group(1)
        extra = ''
        if len(ex_date) == 7:
            extra = ex_date[0]

        return extra

    @staticmethod
    def change_extra(c, extra):
        """
        Change option_code from normal or exists extra into another
        :param c: str
        :param extra: str/int
        :return: str
        """
        symbol = re.search('^([A-Z]+)\d+[CP]+\d+', c).group(1)
        ex_date = re.search('^[A-Z]+(\d+)[CP]+\d+', c).group(1)
        if len(ex_date) != 7:
            raise ValueError('Only can change extra on a split/others codes')
        # old_extra = ex_date[0]
        ex_date = ex_date[-6:]
        name = re.search('^[A-Z]+\d+([CP]+)\d+', c).group(1)

        if '.' in c:
            strike = re.search('^[A-Z]+\d+[CP]+(\d*[.]\d+)', c).group(1)
        else:
            strike = re.search('^[A-Z]+\d+[CP]+(\d+)', c).group(1)

        new_code = '{symbol}{extra}{ex_date}{name}{strike}'.format(
            symbol=symbol, extra=extra, ex_date=ex_date, name=name, strike=strike
        )

        return new_code

    @staticmethod
    def extra_to_normal(code, strike=''):
        """
        Convert split/others code into normal code
        :param code: str
        :param strike: float
        :return: set (str, TimeStamp, str, float)
        """
        symbol = re.search('^([A-Z]+)\d+[CP]+\d+', code).group(1)
        ex_date = re.search('^[A-Z]+(\d+)[CP]+\d+', code).group(1)
        if len(ex_date) != 7:
            raise ValueError('Only can convert a split/others codes')
        ex_date = ex_date[-6:]
        name = re.search('^[A-Z]+\d+([CP]+)\d+', code).group(1)

        if strike == '':
            if '.' in code:
                strike = re.search('^[A-Z]+\d+[CP]+(\d*[.]\d+)', code).group(1)
            else:
                strike = re.search('^[A-Z]+\d+[CP]+(\d+)', code).group(1)

        normal_code = '{symbol}{ex_date}{name}{strike}'.format(
            symbol=symbol, ex_date=ex_date, name=name, strike=strike
        )

        return normal_code

    @staticmethod
    def match(symbol, others):
        """
        Find others is exactly a split
        :param symbol: str
        :param others: str
        :return: bool
        """
        result = False
        if RIGHT_OTHERS.search(others):
            items = others.split(' ')
            if symbol == items[0]:
                result = True
        return result


class GroupOption(object):
    """
    Grouping raw option data
    """
    def __init__(self, symbol, df_stock, split_history):
        """
        :param symbol: str
        :param df_stock: pd.DataFrame
        """
        self.symbol = symbol.upper()
        self.require_length = len(self.symbol) + MIN_LENGTH
        self.df_stock = df_stock.sort_index(ascending=False)
        self.df_all = pd.DataFrame()
        self.split_history = split_history

        self.db_path = os.path.join(CLEAN_DIR, '__%s__.h5' % self.symbol.lower())

    def convert_data(self):
        """
        Get data from thinkback file and make df_all
        """
        print '=' * 70
        print output % ('GET', 'Option data:', self.symbol.upper())
        print '=' * 70

        db = pd.HDFStore(self.db_path)
        try:
            # raise KeyError
            self.df_all = db['all']
            # logger.info('Get data from clean: %s' % self.db_path)
            print output % ('SKIP', 'Read from clean, df_all: %d' % len(self.df_all), '')
        except KeyError:
            symbol0 = self.symbol.lower()
            symbol1 = self.symbol.upper()

            options = []
            path = os.path.join(THINKBACK_DIR, symbol0)
            # logger.info('Get data from path: %s' % path)
            for key in np.arange(len(self.df_stock)):
                # open path get option data
                date = ds(self.df_stock.index[key].date())
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

            self.df_all = df_all.sort_values('date')

            db = pd.HDFStore(self.db_path)
            db['all'] = df_all
        db.close()

        print '=' * 70

    def prepare_extra(self):
        """
        Some split/others have duplicate extra
        check exact result before major update code
        All date without duplicate extra 1-7 only
        """
        print '-' * 70
        print output % ('PROC', 'split/others option_code update', '')
        print '-' * 70
        df_all = self.df_all
        group = df_all.query('right != "100" | others != ""').groupby(['right', 'others'])

        df_date = pd.concat([group['date'].min(), group['date'].max()], axis=1)
        """:type: pd.DataFrame"""
        df_date.columns = ['start', 'stop']
        df_date = df_date.sort_values('stop', ascending=False)

        df_date['extra'] = 0
        for (right0, others0), (start0, stop0, _) in df_date.iterrows():
            print '-' * 70
            print output % ('CODE', 'update split: %s, others: %s' % (right0, others0), '')
            print '-' * 70
            df_current = group.get_group((right0, others0)).sort_values('date', ascending=False)
            data = df_current.iloc[0]

            try:
                extra0 = CodeChanger.get_extra(data['option_code'])
                if extra0 == '':
                    raise AttributeError
                print output % ('EXTRA', 'latest extra in codes:', extra0)
            except AttributeError:
                if '; US$' in others0:
                    extra0 = 2
                else:
                    # estimate extra that no duplicate in date range
                    not_extras = []
                    for (right1, others1), (start1, stop1, extra1) in df_date.iterrows():
                        if right0 == right1 and others0 == others1:
                            continue

                        if start1 <= start0 <= stop1 or start1 <= stop0 <= stop1:
                            not_extras.append(int(extra1))

                    extra0 = [i for i in range(1, 7) if i not in not_extras][0]
                    print output % ('EXTRA', 'use estimate extra:', extra0)

            df_date.loc[(right0, others0), 'extra'] = str(extra0)

            print output % ('CODE', 'using extra:', extra0)

            # update split/others first before major update
            df_current['update'] = df_current['option_code'].apply(
                lambda x: True if len(x) < self.require_length else (
                    False if self.symbol in x else True
                )
            )

            df_group = df_current.groupby('option_code').first()[[
                'others', 'right', 'special', 'ex_date', 'name', 'strike'
            ]]

            replace_codes = {}
            for code, data in df_group.iterrows():
                data['option_code'] = code
                replace_codes[code] = CodeChanger.code_change(
                    data, self.symbol, self.require_length, extra0
                )

            print '-' * 70
            print output % ('CODE', 'total update codes:', len(replace_codes))

            df_current['option_code'] = df_current['option_code'].apply(
                lambda x: replace_codes[x]
            )

            # ts(df_change.head(100))
            print '-' * 70
            print output % ('CODE', 'total update rows:', len(df_current))
            print '-' * 70

            # save back into df_all
            del df_current['update']
            df_remain = df_all[~df_all.index.isin(df_current.index)]
            df_all = pd.concat([df_current, df_remain])
            """:type: pd.DataFrame"""

        self.df_all = df_all

        return df_date

    def update_code(self):
        """
        Major update all old_code or no symbol code into new format
        """
        print '-' * 70
        print output % ('PROC', 'major option_code update', '')
        print '-' * 70

        df_all = self.df_all
        """:type: pd.DataFrame"""

        df_all['update'] = df_all['option_code'].apply(
            lambda x: True if len(x) < self.require_length else (
                False if self.symbol in x else True
            )
        )
        df_remain = df_all[~df_all['update']].copy()
        df_change = df_all[df_all['update']].copy()

        df_group = df_change.groupby('option_code').first()[[
            'others', 'right', 'special', 'ex_date', 'name', 'strike'
        ]]

        replace_codes = {}
        for code, data in df_group.iterrows():
            data['option_code'] = code
            replace_codes[code] = CodeChanger.code_change(data, self.symbol, self.require_length)

        print '-' * 70
        print output % ('CODE', 'total update codes:', len(replace_codes))

        df_change['option_code'] = df_change['option_code'].apply(
            lambda x: replace_codes[x]
        )
        # ts(df_change.head(100))
        print '-' * 70
        print output % ('CODE', 'total update rows:', len(df_change))
        print '-' * 70

        # only unique code is change
        df_new = pd.concat([df_change, df_remain])
        """:type: pd.DataFrame"""

        group = df_new.groupby(['option_code', 'date'])
        size = group.size()
        if len(size[size == 2]):
            prob_size = size[size == 2]
            ts(df_new.query(
                'option_code == %r & date == %r' % (prob_size.index[0][0], prob_size.index[0][1])
            ))
            # identify using latest records
            raise IndexError('Duplicated code still found')

        del df_new['update']
        self.df_all = df_new

    def check_code_no_extra(self):
        """
        For GOOG, when new_code have no extra
        GOOG150515C790 got other
        1. find no extra codes
        2. use code to get original code
        3. replace all in df_change
        """
        print '-' * 70
        print output % ('PROC', 'change no extra code when split/others exists', '')
        print '-' * 70

        df_all = self.df_all
        """:type: pd.DataFrame"""

        for query in ('others != ""', 'right != "100"'):
            print output % ('QUERY', 'str: %s' % query, '')
            df_check = df_all.query(query)
            others_codes = df_check['option_code'].unique()
            update_codes = [c for c in others_codes if not CodeChanger.got_extra(c)]

            if len(update_codes):
                df_update = df_check[df_check['option_code'].isin(update_codes)]
                group0 = df_update.groupby('option_code')
                df_search = df_check[~df_check.index.isin(df_update.index)]
                group1 = df_search.groupby('index2')

                replace_codes = {}
                for code0 in update_codes:
                    data = group0.get_group(code0).iloc[0]
                    print output % ('CODE', 'code0: %s, index2: %s' % (code0, data['index2']), '')

                    try:
                        code1 = group1.get_group(data['index2']).iloc[0]['option_code']
                        print output % ('CODE', 'code0: %s ->' % code0, 'code1: %s' % code1)
                        replace_codes[code0] = code1
                    except KeyError:
                        print output % ('WARN', 'no original code found', 'approximate')
                        similar_code = df_all.query('date == %r & right == %r & others == %r' % (
                            data['date'], data['right'], data['others']
                        )).iloc[0]['option_code']
                        extra = CodeChanger.get_extra(similar_code)
                        print output % ('FOUND', 'similar others extra:', extra)

                        code1 = CodeChanger.make_code0(
                            self.symbol, code0,
                            data['others'], data['right'], data['special'],
                            extra
                        )
                        print output % ('CODE', 'code0: %s ->' % code0, 'code1: %s' % code1)
                        replace_codes[code0] = code1

                df_update['option_code'] = df_update['option_code'].apply(
                    lambda x: replace_codes[x] if x in replace_codes.keys() else x
                )

                df_remain = df_all[~df_all.index.isin(df_update.index)]
                df_all = pd.concat([df_update, df_remain])
                """:type: pd.DataFrame"""

        self.df_all = df_all

    @staticmethod
    def others_to_right(data):
        """
        :param data: str
        :return: str
        """
        result = data['right']
        right = re.search('^[A-Z]+\s(\d+)', data['others']).group(1)

        if data['right'] != right:
            result = '%s/100' % re.search('^[A-Z]+\s(\d+)', data['others']).group(1)

        return result

    def modify_others(self):
        """
        Modify some others which is same as split
        VXX 25 or TZA 25 is same as 25/100 right but not PYPL 100
        """
        print '-' * 70
        print output % ('PROC', 'modify others to split', '')
        print '-' * 70
        df_others = self.df_all[self.df_all['others'] != ''].copy()

        if len(df_others):
            df_others['update'] = df_others['others'].apply(
                lambda x: CodeChanger.match(self.symbol, x)
            )
            print output % ('OTHERS', 'df_others length:', len(df_others))

            df_update = df_others[df_others['update']]

            if len(df_update):
                print output % ('OTHERS', 'others that require modify', len(df_update))
                df_update['right'] = df_update.apply(self.others_to_right, axis=1)

                df_update['others'] = ''
                del df_update['update']
                print output % ('OTHERS', 'remove others and keep split', '')
                # ts(df_update)

                df_remain = self.df_all[~self.df_all.index.isin(df_update.index)]
                self.df_all = pd.concat([df_remain, df_update])
                """:type: pd.DataFrame"""

    def remove_duplicate(self):
        """
        Remove duplicated row that have exactly same bid/ask and option_code
        """
        print '-' * 70
        print output % ('PROC', 'remove duplicated rows', '')
        print '-' * 70

        df_all = self.df_all
        """:type: pd.DataFrame"""
        group = df_all.groupby(['option_code', 'date'])
        size = group.size()
        dup_size = size[size > 1]

        remove = []
        for i in np.arange(len(dup_size)):
            # print dup_size.index[i], dup_size[i]
            index = dup_size.index[i]
            df_dup = group.get_group(index)
            print output % ('DUP', '%d. code: %s, date: %s' % (
                i, index[0], ds(index[1])
            ), 'rows: %d' % len(df_dup))

            found = df_dup[df_dup.duplicated()]
            if len(found):
                remove.append(found.index[0])  # always remove second
            else:
                found = df_dup[df_dup[['bid', 'ask', 'option_code']].duplicated()]

                if len(found):
                    # ts(found)
                    print output % ('DUP', 'found using less columns', '')
                    remove.append(found.index[0])
                else:
                    raise ValueError('Real different row code/date found')

        df_all = df_all[~df_all.index.isin(remove)]
        self.df_all = df_all

    def update_non_standard(self):
        """
        Some of the cycle have Non standard in others with split is 100 mostly
        replace them with exact split and others with later cycle
        others: Non Standard
        :return:
        """
        df_non = self.df_all[self.df_all['others'] == 'Non Standard'].copy()
        df_normal = self.df_all[~self.df_all.index.isin(df_non.index)].copy()
        group0 = df_non.sort_values('date').groupby('option_code')
        group1 = df_normal.sort_values('date').groupby('option_code')
        # non_codes = df_non['option_code'].value_counts()
        df_search = df_non.groupby('option_code')['date'].max()

        if len(df_search) == 0:
            print output % ('UPDATE', '"Non Standard" others not found', '')
        else:
            print output % ('UPDATE', 'start update split/others', '"Non Standard"')

        drops = []
        updates = {}
        for code, stop in df_search.iteritems():
            try:
                right, others = group1.get_group(code).query(
                    'date > %r' % stop
                )[['right', 'others']].iloc[0]
                print output % (
                    'NON', 'code: %s, date: %s' % (code, ds(stop)), '(%s, %s)' % (right, others)
                )

                updates[code] = (right, others)
            except (KeyError, IndexError):
                # df_non code not exists in df_normal
                df_code = group0.get_group(code).copy()
                df_code['empty'] = (df_code['ask'] == 0) & (df_code['bid'] == 0)
                if not np.any(df_code['empty']):
                    drops.append(code)

        if len(drops):
            df_non = df_non[~df_non['option_code'].isin(drops)]

        # todo: here, goog

        if len(updates):
            df_non['right'] = df_non.apply(lambda x: updates[x['option_code']][0], axis=1)
            df_non['others'] = df_non.apply(lambda x: updates[x['option_code']][1], axis=1)
            print output % ('NON', 'finish update "Non Standard"', '')
            assert len(df_non[df_non['others'] == 'Non Standard']) == 0
            self.df_all = pd.concat([df_normal, df_non])
            """:type: pd.DataFrame"""
        else:
            self.df_all = self.df_all[~self.df_all['option_code'].isin(drops)]

    def ready_data(self, debug=False):
        """
        Ready data for grouping
        :param debug: True
        :return: None or pd.DataFrame
        """
        self.update_non_standard()
        self.remove_duplicate()
        self.prepare_extra()
        self.update_code()
        self.check_code_no_extra()
        self.modify_others()

        # debug output
        df_date = pd.DataFrame()
        if debug:
            group = self.df_all.query('right != "100" | others != ""').groupby(['right', 'others'])

            if len(group):
                df_date = pd.concat([
                    group['date'].min(),
                    group['date'].max(),
                    group['option_code'].first()
                ], axis=1)
                """:type: pd.DataFrame"""
                df_date.columns = ['start', 'stop', 'option_code']
                df_date['extra'] = df_date['option_code'].apply(
                    lambda c: CodeChanger.get_extra(c)
                )

        # duplicate check
        group = self.df_all.groupby(['option_code', 'date'])
        size = group.size()
        dup_size = size[size > 1]
        if len(dup_size):
            print dup_size
            ts(self.df_all.query(
                'option_code == %r & date == %r' % (dup_size.index[0][0], dup_size.index[0][1])
            ))

        return df_date

    def check_split_others(self):
        """
        Check there is split or others in options
        """
        old_split = [s for s in self.df_all['right'].unique() if s != '100']
        others = [o for o in self.df_all['others'].unique() if o != '']

        print '=' * 70
        print output % ('SPLIT', 'Data: %s' % old_split, '')
        print output % ('OTHERS', 'Data: %s' % others, '')
        print '=' * 70

        proc = 'normal'
        if len(old_split) and len(others):
            print output % ('PROC', 'Complex cleaning process', 'split & others')
            proc = 'complex'
        elif len(old_split) and not len(others):
            print output % ('PROC', 'Middle cleaning process', 'old split only')
            proc = 'old_split'
        elif not len(old_split) and len(others):
            print output % ('PROC', 'Middle cleaning process', 'others only')
            proc = 'others'
        else:
            if len(self.split_history):
                print output % ('PROC', 'Middle cleaning process', 'new split only')
                proc = 'new_split'
            else:
                print output % ('PROC', 'Fast cleaning process', 'normal only')

        return proc

    def get_all(self):
        """
        Get df_all option data
        """
        self.convert_data()
        self.ready_data()

        return self.df_all


class ComplexGroupOptions(object):
    """
    Group data using complex group method
    """
    def __init__(self, symbol, df_all, split_history):
        self.symbol = symbol
        self.df_all = df_all
        self.split_history = split_history

        self.df_normal = pd.DataFrame()

        self.df_remain = pd.DataFrame()
        self.df_both = pd.DataFrame()
        self.df_old_split = pd.DataFrame()
        self.df_others = pd.DataFrame()

        self.df_date = pd.DataFrame()

    def prepare_set(self):
        """
        Split df_all into df_normal and df_remain for better grouping
        """
        self.df_normal = self.df_all.query('right == "100" & others == ""').copy()
        self.df_remain = self.df_all.query('right != "100" | others != ""').copy()
        # print len(self.df_all), len(self.df_normal),  len(df_remain)
        print output % ('DATA', 'df_normal: %d' % len(self.df_normal), '')
        print output % ('DATA', 'df_remain: %d' % len(self.df_remain), '')
        print '-' * 70

    def group_data(self):
        """
        Group split/others/both data in a list of non-duplicate set
        split follow split, normal
        others follow others, normal
        both follow both, split, others, normal
        """
        print output % ('PROC', 'group data', '')
        print '.' * 70

        # drop new split
        df_temp = self.df_remain[self.df_remain['right'].str.contains('/')]
        group = df_temp.groupby(['right', 'others'])
        df_date = pd.concat([group['date'].min(), group['date'].max()], axis=1)
        """:type: pd.DataFrame"""
        df_date.columns = ['start', 'stop']
        df_date = df_date.sort_values('start')

        follows = []
        removes = []
        for (split0, others0), (start0, stop0) in df_date.iterrows():
            print output % ('GROUP', 'check follow:', '(%s, %s)' % (split0, others0))
            print output % ('DATA', 'start: %s' % ds(start0), 'stop: %s' % ds(stop0))

            if split0 and others0 == '':
                # split section
                split1, others1 = self.check_split(df_date, split0, start0)
                follows.append((split1, others1))
            elif split0 == '100' and others0:
                # others section
                split1, others1 = self.check_others(df_date, others0, start0)
                follows.append((split1, others1))
            elif split0 != '100' and others0:
                # both section
                split1, others1 = self.check_both(df_date, others0, split0, start0)
                follows.append((split1, others1))
            else:
                raise ValueError('Invalid split/others in df_date')

            # if split is same, others different, but follow, update self remain
            if split0 == split1 and others0 != others1:
                print output % ('REMOVE', 'split same, others different', 'del df_date row')
                # remove row in df_date
                removes.append((split1, others1))
                print output % ('DEL', 'remove follow in df_date:', '(%s, %s)' % (split1, others1))

                # update df_remain
                self.df_remain['others'] = self.df_remain['others'].apply(
                    lambda x: others0 if x == others1 else x
                )
                print output % (
                    'UPDATE', '(%s, %s) ->' % (split1, others1), '(%s, %s)' % (split0, others0)
                )

            print '.' * 70

        # add follow, update date for remove rows
        df_date['follow'] = follows
        for (split0, others0), (start0, stop0, (split1, others1)) in df_date.iterrows():
            if split1 != '' and others1 != '':
                print output % ('UPDATE', 'update start, stop', 'before remove follow')
                print output % ('GROUP', 'split: %s' % split0, 'others: %s' % others0)
                print output % ('DATA', 'start: %s' % ds(start0), 'stop: %s' % ds(stop0))
                print output % ('ROW', 'get follow data', '(%s, %s)' % (split1, others1))
                row = df_date.ix[(split1, others1)]

                index = (split0, others0)
                df_date.loc[index, 'start'] = row['start'] if start0 > row['start'] else start0
                df_date.loc[index, 'stop'] = row['stop'] if stop0 < row['stop'] else stop0
                print output % ('UPDATE', 'start: %s ->' % ds(start0), ds(df_date.loc[index, 'start']))
                print output % ('UPDATE', 'stop: %s ->' % ds(stop0), ds(df_date.loc[index, 'stop']))
                print '.' * 70

        # remove others rows and follow
        df_date = df_date[~df_date.index.isin(removes)]
        df_date['follow'] = df_date['follow'].apply(
            lambda x: ('', '') if x in removes else x
        )

        self.df_date = df_date

    def check_both(self, df_date, others0, split0, start0):
        """
        Both split & others can have 4 possible follow
        1. split/others both
        2. others only
        3. split only
        4. normal only
        :param df_date: pd.DataFrame
        :param others0: str
        :param split0: str
        :param start0: pd.datetime
        :return: str, str
        """
        print output % ('SUB', 'got both, follow ->', 'others, split, normal')
        from_start = start0 - BDay(5)
        to_stop = start0 + BDay(5)
        df_cont = df_date[
            (df_date['stop'] >= from_start) & (df_date['stop'] <= to_stop)
        ]

        follow = ('', '')
        if len(df_cont) == 0:
            print output % ('EMPTY', 'no df_count found', len(df_cont))

        for (split1, others1), (start1, stop1) in df_cont.iterrows():
            print output % ('FOLLOW', 'check follow:', '(%s, %s)' % (split1, others1))
            print output % ('DATA', 'start: %s' % ds(start1), 'stop: %s' % ds(stop1))

            # option_code find
            df_both = self.df_remain.query('right == %r & others == %r & date == %r' % (
                split0, others0, start0
            ))[['option_code']]

            df_find = self.df_remain.query('right == %r & others == %r & date == %r' % (
                split1, others1, stop1
            ))[['option_code']]

            codes0 = list(df_both['option_code'])
            codes1 = list(df_find['option_code'])

            found = 0
            for code in codes0:
                if code in codes1:
                    found += 1

            # option code find
            if found == len(codes0):
                print output % ('CHECK', 'option_code found', '100%')
                follow = (split1, others1)
                break
            elif found >= len(codes0) * 0.5:
                print output % ('CHECK', 'option_code found', '50%')
                follow = (split1, others1)
                break

            # name find
            if split0 == split1:  # from both to split
                print output % ('CHECK', 'split similar found: %s ==' % split0, split1)
                follow = (split1, others1)
                break
            elif others0 == others1:  # from both to others
                print output % ('CHECK', 'others similar found: %s ==' % others0, others1)
                follow = (split1, others1)
                break
            else:  # no found, from both to normal
                print 'continue both not found'

        if follow[0] == '' and follow[1] == '':
            print 'possible code change and split/others change too???'

        return follow

    def check_others(self, df_date, others0, start0):
        """
        Check others follow by others, normal
        :param df_date: pd.DataFrame
        :param others0: str
        :param start0: pd.datetime
        :return: str, str
        """
        print output % ('SUB', 'only others follow ->', 'others, normal')
        from_start = start0 - BDay(5)
        to_stop = start0 + BDay(5)
        df_cont = df_date[
            (df_date['stop'] >= from_start) & (df_date['stop'] <= to_stop)
        ]

        follow = ('', '')
        if len(df_cont) == 0:
            print output % ('EMPTY', 'no df_count found', len(df_cont))

        for (split1, others1), (start1, stop1) in df_cont.iterrows():
            print output % ('FOLLOW', 'check follow:', '(%s, %s)' % (split1, others1))
            print output % ('DATA', 'start: %s' % ds(start1), 'stop: %s' % ds(stop1))

            # option_code find
            df_both = self.df_remain.query('others == %r & date == %r' % (
                others0, start0
            ))[['option_code']]

            df_find = self.df_remain.query('others == %r & date == %r' % (
                others1, stop1
            ))[['option_code']]

            codes0 = list(df_both['option_code'])
            codes1 = list(df_find['option_code'])

            found = 0
            for code in codes0:
                if code in codes1:
                    found += 1

            if found == len(codes0):
                print output % ('CHECK', 'option_code found', '100%')
                follow = (split1, others1)
                break
            elif found >= len(codes0) * 0.5:
                print output % ('CHECK', 'option_code found', '50%')
                follow = (split1, others1)
                break

        return follow

    def check_split(self, df_date, split0, start0):
        """
        Check split follow by split, normal
        :param df_date: pd.DataFrame
        :param split0: str
        :param start0: pd.datetime
        :return: str, str
        """
        print output % ('SUB', 'only split follow ->', 'split, normal')
        from_start = start0 - BDay(5)
        to_stop = start0 + BDay(5)
        df_cont = df_date[
            (df_date['stop'] >= from_start) & (df_date['stop'] <= to_stop)
        ]

        follow = ('', '')
        if len(df_cont) == 0:
            print output % ('EMPTY', 'no df_count found', len(df_cont))

        for (split1, others1), (start1, stop1) in df_cont.iterrows():
            print output % ('FOLLOW', 'check follow:', '(%s, %s)' % (split1, others1))
            print output % ('DATA', 'start: %s' % ds(start1), 'stop: %s' % ds(stop1))

            # option_code find
            df_both = self.df_remain.query('right == %r & date == %r' % (
                split0, start0
            ))[['option_code']]

            df_find = self.df_remain.query('right == %r & date == %r' % (
                split1, stop1
            ))[['option_code']]

            codes0 = list(df_both['option_code'])
            codes1 = list(df_find['option_code'])

            found = 0
            for code in codes0:
                if code in codes1:
                    found += 1

            if found == len(codes0):
                print output % ('CHECK', 'option_code found', '100%')
                follow = (split1, others1)
                break
            elif found >= len(codes0) * 0.5:
                print output % ('CHECK', 'option_code found', '50%')
                follow = (split1, others1)
                break

        return follow

    def others_is_split(self):
        """
        Check others is actually split, example: TZA 25 others is 25/100 split
        After found, remove others in df_remain and update df_date
        """
        print output % ('PROC', 'check others is split', '')
        print '.' * 70
        df_date = self.df_date
        df_date['remove_others'] = False

        for (split0, others0), (start, stop, (split1, others1), _) in df_date.iterrows():
            print output % ('CHECK', 'split is others', '(%s, %s)' % (split0, others0))

            is_split = False
            need_check = False
            # check current is split
            if others0 != '':
                if SPLIT_FORMAT0.search(others0) or SPLIT_FORMAT1.search(others0):
                    need_check = True

            if need_check:
                # check previous is split
                if split1 or others1:
                    print output % ('CHECK', 'check follow is split or not', '')
                    if df_date.loc[(split1, others1), 'remove_others']:
                        print output % ('CHECK', 'previous follow is split', 'set true')
                        is_split = True

                # check dates
                if not is_split:
                    print output % ('CHECK', 'date range got split_history', '')
                    date0 = (start - BDay(5)).date()
                    date1 = (stop + BDay(5)).date()

                    remove_others = False
                    for history in self.split_history:
                        print output % ('SPLIT', 'check history', history)
                        if date0 <= history.date <= date1:
                            print output % ('CHECK', 'date within split_history found', 'set true')
                            remove_others = True
                            break

                    if remove_others:
                        print output % ('CHECK', 'others is actually split', '')
                        print output % ('CHECK', 'others: %s is remove' % others0, '')
                        print output % ('CHECK', 'split: %s is keep' % split0, '')
                        is_split = True

            df_date.loc[(split0, others0), 'remove_others'] = is_split

            print '.' * 70

        # start remove in df_all
        if len(df_date[df_date['remove_others']]):
            remove_list = list(df_date[df_date['remove_others']].index.get_level_values('others'))

            df_keep = self.df_remain[~self.df_remain['others'].isin(remove_list)]
            df_update = self.df_remain[self.df_remain['others'].isin(remove_list)]
            print output % ('UPDATE', 'df_others that remove others', len(df_update))

            df_update['others'] = ''

            self.df_remain = pd.concat([df_keep, df_update])
            """:type: pd.DataFrame"""

    def join_data(self):
        """
        :return:
        """
        print output % ('PROC', 'split/others join previous df_normal data', '')
        print '=' * 70

        # first asc order
        df_date = self.df_date.sort_values('start')
        # ts(df_date)

        # join data with normal
        df_list = {}
        for (split0, others0), (start, stop, (split1, others1)) in df_date.iterrows():
            remove_index = []
            print output % ('DATA', 'split0: %s' % split0, 'others0: %s' % others0)
            print output % ('DATE', 'start: %s' % ds(start), 'stop: %s' % ds(stop))
            key0 = '%s,%s' % (split0, others0)
            df_current = self.df_remain.query('right == %r & others == %r' % (split0, others0))
            self.df_remain = self.df_remain[~self.df_remain.index.isin(df_current.index)]
            print output % ('DATA', 'df_current: %d' % len(df_current), '')
            print output % ('DATA', 'df_remain: %d' % len(self.df_remain), '')

            if split1 == '' and others1 == '':
                print output % ('FIND', 'search old df_normal data', '')
                current_codes = df_current['option_code'].unique()
                replace_codes = {CodeChanger.change_extra(c, ''): c for c in current_codes}
                df_before = self.df_normal.query('date < %r' % start)
                df_continue = df_before[df_before['option_code'].isin(replace_codes.keys())].copy()
                df_continue['option_code'] = df_continue['option_code'].apply(
                    lambda code: replace_codes[code]
                )

                if len(df_continue):
                    remove_index += list(df_continue.index)

                print output % (
                    'CONT', 'df_current: %d' % len(df_current), 'df_continue: %d' % len(df_continue)
                )

                df_current = pd.concat([df_current, df_continue])
                """:type: pd.DataFrame"""
                df_list[key0] = df_current
            else:
                print output % ('SKIP', 'got follow, join data later', '')
                print output % ('DATA', 'split1: %s' % split1, 'others1: %s' % others1)
                df_list[key0] = df_current
                print output % ('CONT', 'df_current: %d' % len(df_current), 'df_continue: 0')

            print '-' * 70

            # remove df_normal
            if len(remove_index):
                print output % ('DEL', 'df_normal remove: %d' % len(remove_index), '')
                length0 = len(self.df_normal)
                self.df_normal = self.df_normal[~self.df_normal.index.isin(remove_index)]
                print output % (
                    'DATA', 'df_normal0: %d' % length0, 'df_normal1: %d' % len(self.df_normal)
                )
                assert len(remove_index) == length0 - len(self.df_normal)
                print '-' * 70

        # print len(pd.concat(df.values())), len(self.df_remain)
        print output % ('SUB', 'join all follow data', '')
        print output % ('DATA', 'df_remain: %d' % len(self.df_remain), '')
        print '-' * 70

        if len(self.df_remain):
            if np.any(self.df_remain['right'].apply(lambda x: '/' in x)):
                raise LookupError('df_remain still exists: %d' % len(self.df_remain))
            else:
                print output % ('SPLIT', 'df_remain contain new split', '')
                print '-' * 70

        # desc orders
        df_date = self.df_date.sort_values('start', ascending=False)

        # join follow data
        for (split0, others0), (start, stop, (split1, others1)) in df_date.iterrows():
            key0 = '%s,%s' % (split0, others0)
            if key0 not in df_list.keys():
                continue

            print output % ('DATA', 'split0: %s' % split0, 'others0: %s' % others0)
            print output % ('DATE', 'start: %s' % ds(start), 'stop: %s' % ds(stop))

            if split1 == '' and others1 == '':
                print output % ('END', 'no follow', 'df_current: %d' % len(df_list[key0]))
            else:
                print output % ('FOLLOW', 'continue follow data', '')
                print output % ('DATA', 'split1: %s' % split1, 'others1: %s' % others1)
                df_current = df_list[key0]
                print output % ('START', 'df_current: %d' % len(df_current), '')

                follows = []
                search_split = split1
                search_others = others1
                keep_follow = True
                while keep_follow:
                    row = df_date.ix[(search_split, search_others)]
                    key1 = '%s,%s' % (search_split, search_others)
                    df_follow = df_list[key1]
                    del df_list[key1]

                    if row['follow'][0] == '' and row['follow'][1] == '':
                        print output % (
                            'END', 'no continue follow found', 'df_follow: %d' % len(df_follow)
                        )
                        keep_follow = False
                    else:
                        print output % ('CONT', 'still have follow data', 'continue...')
                        search_split = split1
                        search_others = others1

                    # check extra is same, add into list, then end join df_current
                    current_extras = pd.Series(
                        [CodeChanger.get_extra(c) for c in df_current['option_code'].unique()]
                    ).unique()
                    follow_extras = pd.Series(
                        [CodeChanger.get_extra(c) for c in df_follow['option_code'].unique()]
                    ).unique()

                    for extra in current_extras:
                        if extra not in follow_extras:
                            ts(df_current.head())
                            ts(df_follow.head())
                            raise ValueError(
                                'Invalid extra in option_code current: %s, follow: %s' % (
                                    current_extras, follow_extras
                                )
                            )

                    follows.append(df_follow)

                if len(follows):
                    df_key = pd.concat([df_current] + follows)
                    """:type: pd.DataFrame"""
                    df_key = df_key.sort_values(['date', 'option_code'], ascending=False)
                    df_list[key0] = df_key
                    print output % ('END', 'df_current + df_follow: %d' % len(df_list[key0]), '')

            print '-' * 70

        # double check
        # print len(self.df_normal) + sum([len(v) for k, v in df_list.items()]), len(self.df_all)
        assert ((len(self.df_normal) + sum([len(v) for k, v in df_list.items()]) +
                 len(self.df_remain)) == len(self.df_all))

        return df_list

    def new_split(self):
        """
        After remove old_split/others and remain normal
        use split history to determine new split data
        :return: pd.DataFrame
        """
        print output % ('PROC', 'new split section', '')
        print '=' * 70

        data = []
        for split in self.split_history:
            print output % ('SPLIT', 'history: ', split)
            print '-' * 70

            # get yesterday
            previous_dates = self.df_normal[self.df_normal['date'] < split.date]['date'].unique()
            previous_dates.sort()
            # using 2-days because mostly yesterday have no data
            yesterday = pd.to_datetime(previous_dates)[-2]
            df_yesterday = self.df_normal[self.df_normal['date'] == yesterday]
            print output % ('DATA', 'yesterday: %s' % ds(yesterday), '')
            # ts(df_yesterday)

            # get current split date
            df_current = self.df_remain[self.df_remain['date'] == split.date].copy()
            df_current['strike1'] = df_current['strike'] * Fraction(split.fraction)
            df_current['strike1'] = np.round(df_current['strike1'].astype('float64'), 2)
            strikes = []
            for strike in df_current['strike1']:
                strike_str = '%.2f' % strike
                if strike_str[-2:] in ('99', '01'):
                    strike = round(strike)
                elif strike_str[-2:] in ('49', '51'):
                    strike = round(strike, 1)
                elif strike_str[-2:] in ('26', '24'):
                    strike = '%s.25' % strike_str[:-2]

                strike = float(strike)
                if strike == int(strike):
                    strikes.append('%d' % strike)
                elif strike == round(strike, 1):
                    strikes.append('%.1f' % strike)
                else:
                    strikes.append('%.2f' % strike)

            df_current['strike2'] = strikes

            old_codes0 = list(df_yesterday['option_code'])
            old_codes1 = df_current.apply(
                lambda c: CodeChanger.extra_to_normal(
                    code=c['option_code'], strike=c['strike2']
                ),
                axis=1
            )

            print output % ('CHECK', 'new split code update', '')
            code_updates = {}
            for x, y in zip(old_codes1, df_current['option_code']):
                print output % ('CODE', 'convert back: %s ->' % x, '%s' % y)

                if x in old_codes0:
                    code_updates[x] = y
                    print output % ('FOUND', 'old_code found in df_normal', '')
                else:
                    print output % ('EMPTY', 'old_code NOT FOUND in df_normal!', '')

            df_previous = self.df_normal[
                self.df_normal['option_code'].isin(code_updates.keys())
            ].copy()
            df_previous['new_code'] = df_previous['option_code'].apply(
                lambda c: code_updates[c] if c in code_updates.keys() else c
            )

            df_after = self.df_remain[
                self.df_remain['option_code'].isin(code_updates.values())
            ].copy()

            df_after['new_code'] = df_after['option_code']
            # df = pd.concat([df_previous, df_current])
            # """:type: pd.DataFrame"""
            data.append(df_previous)
            data.append(df_after)

            print '-' * 70
            print output % ('DATA', 'df_previous: %d' % len(df_previous), 'df_after: %d' % len(df_after))

            if len(df_previous):
                self.df_normal = self.df_normal[~self.df_normal.index.isin(df_previous.index)]

            if len(df_after):
                self.df_remain = self.df_remain[~self.df_remain.index.isin(df_after.index)]

        df_split2 = pd.DataFrame()
        if len(data):
            # concat all
            df_split2 = pd.concat(data)
            """:type: pd.DataFrame"""

            df_split2 = df_split2.sort_values(['date', 'new_code'])

            print output % ('DATA', 'df_normal: %d' % len(self.df_normal), '')
            print output % ('DATA', 'df_remain: %d' % len(self.df_remain), '')

            # make sure no more new split
            assert len(self.df_remain) == 0

        return df_split2

    def final_data(self):
        """
        Run all process and return df_normal, df_list (split/others)
        :return: pd.DataFrame, pd.DataFrame
        """
        self.prepare_set()
        self.group_data()
        self.others_is_split()
        self.group_data()
        df_list = self.join_data()
        df_split2 = self.new_split()

        # remove index
        del self.df_normal['index'], self.df_normal['index2']
        for df in df_list.values():
            del df['index'], df['index2']

        return self.df_normal, df_list, df_split2


class ThinkbackOption(object):
    def __init__(self, symbol):
        self.symbol = symbol.upper()
        self.db_path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())
        self.clean_path = os.path.join(CLEAN_DIR, '__%s__.h5' % self.symbol.lower())
        self.df_stock = pd.DataFrame()
        self.split_history = []

        # for update log
        self.df_normal = pd.DataFrame()
        self.df_others = pd.DataFrame()
        self.df_split1 = pd.DataFrame()
        self.df_split2 = pd.DataFrame()

    def get_stock(self):
        """
        Get df_stock data
        """
        db = pd.HDFStore(self.db_path)
        try:
            self.df_stock = db.select('stock/thinkback')
        except KeyError:
            raise KeyError('Please import df_stock first')
        db.close()

    def get_split_history(self):
        """
        Get split history data
        """
        self.split_history = SplitHistory.objects.filter(
            Q(symbol=self.symbol.upper()) & Q(date__gte=self.df_stock.index.min())
        )
        print output % ('GET', 'Split history: %d' % len(self.split_history), '')
        for split in self.split_history:
            print output % ('SPLIT', 'history: ', split)
        print '=' * 70

    def create_raw(self):
        """
        Create option raw data that ready for all continue process
        """
        # prepare data
        self.get_stock()
        self.get_split_history()

        # group option
        group_option = GroupOption(self.symbol, self.df_stock, self.split_history)
        df_all = group_option.get_all()
        proc = group_option.check_split_others()

        # get data
        df_others = pd.DataFrame()
        df_split1 = pd.DataFrame()
        df_split2 = pd.DataFrame()
        if proc == 'normal':
            df_normal = df_all
        else:
            # complex group
            complex_group = ComplexGroupOptions(self.symbol, df_all, self.split_history)
            df_normal, df_list, df_split2 = complex_group.final_data()

            if len(complex_group.df_date):
                ts(complex_group.df_date)

            for df in df_list.values():
                rights = [r for r in df['right'].unique() if r != '100']
                others = [o for o in df['others'].unique() if o != '']

                if (len(rights) and len(others)) or len(others):
                    df_others = pd.concat([df_others, df])
                elif len(rights):
                    df_split1 = pd.concat([df_split1, df])
                else:
                    raise LookupError('Invalid process result no split/others df_list')

            print '=' * 70
            print output % ('IMPORT', 'Complete extract option data', '')
            print '=' * 70
            print output % ('STAT', 'df_normal length: %d' % len(df_normal), '')
            print output % ('STAT', 'df_others length: %d' % len(df_others), '')
            print output % ('STAT', 'df_split1 length: %d' % len(df_split1), '')
            print output % ('STAT', 'df_split2 length: %d' % len(df_split2), '')

        # saving
        logger.info('Save data into clean, path: %s' % self.clean_path)
        db = pd.HDFStore(self.clean_path)
        try:
            db.remove('option/raw')
        except KeyError:
            pass

        db.append('option/raw/normal', df_normal)

        if len(df_others):
            db.append('option/raw/others', df_others)

        if len(df_split1):
            db.append('option/raw/split/old', df_split1)

        if len(df_split2):
            db.append('option/raw/split/new', df_split2)
        db.close()

        print output % ('SAVE', 'All data saved', '')
        logger.info('Complete save raw options')

        self.df_normal = df_normal
        self.df_others = df_others
        self.df_split1 = df_split1
        self.df_split2 = df_split2

    def update_underlying(self):
        """
        Update underlying after completed
        """
        Underlying.write_log(self.symbol, [
            'Raw df_normal length: %d' % len(self.df_normal),
            'Raw df_others length: %d' % len(self.df_others),
            'Raw df_split/old length: %d' % len(self.df_split1),
            'Raw df_split/new length: %d' % len(self.df_split2)
        ])
