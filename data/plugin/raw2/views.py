import calendar
import logging
import pandas as pd
import re
import os
from data.models import SplitHistory
from data.plugin.thinkback import ThinkBack
from django.db.models import Q
from django.shortcuts import redirect
from fractions import Fraction
from rivers.settings import QUOTE, BASE_DIR

# constant for get_dte_date
logger = logging.getLogger('views')
output = '%-6s | %-30s %s'
calendar.setfirstweekday(calendar.SUNDAY)
month_abbr = [calendar.month_abbr[i].upper() for i in range(1, 13)]
months = {
    '%d-%d' % (y, m): calendar.monthcalendar(y, m) for m in range(1, 13) for y in range(8, 20)
}


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
        ex_date = pd.Timestamp(get_dte_date2(contract['ex_month'], int(contract['ex_year'])))

        new_code = make_code2(
            symbol, contract['others'], contract['right'], contract['special'],
            ex_date, contract['name'], contract['strike']
        )
        print output % ('CODE', 'Update (old format):', '%-16s -> %-16s' % (
            contract['option_code'], new_code
        ))
    elif contract['option_code'][:len(symbol)] != symbol.upper():
        # some ex_date is on thursday because holiday or special date
        new_code = change_code(
            symbol, contract['option_code'], contract['others'], contract['right'], contract['special']
        )
        print output % ('CODE', 'Update (no symbol):', '%-16s -> %-16s' % (
            contract['option_code'], new_code
        ))
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
        'ex_month', 'ex_year', 'name', 'option_code',
        'others', 'right', 'special', 'strike'
    ]]


class ExtractOption(object):
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

    def get_data(self):
        """
        Get data from thinkback file and make df_all
        """
        print '=' * 130
        print output % ('FIELD', 'Get data from csv files', '')
        print '=' * 130

        symbol = self.symbol.lower()

        options = []
        # noinspection PyUnresolvedReferences
        path = os.path.join(BASE_DIR, 'files', 'thinkback', symbol)
        for no, (index, values) in enumerate(self.df_stock.iterrows()):
            # open path get option data
            year = index.date().strftime('%Y')
            fpath = os.path.join(
                path, year, '%s-StockAndOptionQuoteFor%s.csv' % (
                    index.date().strftime('%Y-%m-%d'), symbol.upper()
                )
            )
            print output % (no, 'read file for option data:', os.path.basename(fpath))
            _, data = ThinkBack(fpath).read()

            for c, o in data:
                c['ex_date'] = get_dte_date2(c['ex_month'], c['ex_year'])

                c['index'] = '%s%s%s%s' % (
                    c['ex_month'], c['ex_year'], c['name'], c['strike']
                )
                c['index2'] = '%s%s%s%s_%s_%s' % (
                    c['ex_month'], c['ex_year'], c['name'], c['strike'], c['right'], c['others']
                )

                o.update(c)
                options.append(o)

        # make all options df
        df_all = pd.DataFrame(options)
        df_all['date'] = pd.to_datetime(df_all['date'])
        df_all['ex_date'] = pd.to_datetime(df_all['ex_date'])

        self.df_all = df_all

    def group_data(self):
        """
        Group data base on normal, split or others
        """
        print '=' * 130
        print output % ('FIELD', 'Group raw data base on', 'normal, split, others')
        print '=' * 130

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

    def merge_old_split_data(self):
        """
        Split is always merge with normal data
        because old data is always normal
        but others can be split then become others
        """
        print '=' * 130
        print output % ('FIELD', 'Merge old split data', '')
        print '=' * 130

        print 'df_split length: %d' % len(self.df_split0)
        print '-' * 100

        if len(self.df_split0):
            data = []
            for index in self.df_split0['index'].unique():
                print output % ('SPLIT', 'Get row data for split', 'index: %s' % index)
                df_current = self.df_split0.query('index == %r' % index).copy()
                """:type: pd.DataFrame"""
                # print df_current.to_string(line_width=1000)

                if len(df_current) != len(df_current['date'].unique()):
                    print df_current.to_string(line_width=1000)
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
                print '-' * 100

            print 'df_split length: %d' % len(self.df_split0)

            df_split = pd.concat(data)
            """:type: pd.DataFrame"""
            df_split = df_split.sort_values('date', ascending=False)

            self.df_split1 = df_split

    def merge_others_data(self):
        """
        Others is always old format, new format got no others or right
        """
        print '=' * 130
        print output % ('FIELD', 'Merge old others data', '')
        print '=' * 130

        print 'df_others length: %d' % len(self.df_others0)

        # codes = df_others['option_code'].unique()
        # df_others = df_others[df_others['index'] == 'JAN11PUT2.5']
        # print df_others.to_string(line_width=1000)
        # print df_normal[df_normal['index'] == 'JAN11PUT2.5'].to_string(line_width=1000)

        if len(self.df_others0):
            group = self.df_others0.groupby('index2')
            dates = pd.Series(group['date'].max()).sort_values(ascending=False)
            # print dates

            data = []
            for index2, date in dates.iteritems():
                print output % (
                    'START', 'index2: %s ' % index2, 'date: %s' % date.strftime('%Y-%m-%d')
                )
                df_current = self.df_others0.query('index2 == %r & date == %r' % (index2, date))

                if len(df_current) == 0:
                    print output % ('EMPTY', 'No more others data (added)', '')
                    print '-' * 100
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
                        print output % ('OTHERS', 'Duplicate date in others continue data', '')
                        for key, value in [('option_code', code), ('right', right)]:
                            df_similar = df_continue[df_continue[key] == value]

                            if len(df_similar):
                                print output % ('OTHERS', 'Found others continue data using',
                                                '%s: %s' % (key, value))
                                df_current = pd.concat([df_current, df_similar])
                                self.df_others0 = self.df_others0[~self.df_others0.index.isin(df_similar.index)]
                                break
                        else:
                            # no break, loop until end
                            print output % ('OTHERS', 'Found pass data but have duplicate date', '')
                            df_continue = pd.DataFrame(columns=['index', 'date'])
                    else:
                        print output % ('OTHERS', 'Merge others continue option data', len(df_continue))
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
                    print df_current.to_string(line_width=1000)
                    raise LookupError('Duplicate date!!!')

                # update code
                contract = get_contract(df_current)
                new_code = check_code(self.symbol, contract)
                df_current['option_code'] = new_code
                print output % ('CODE', 'using option_code:', new_code)

                # done, append into data
                data.append(df_current)
                print '-' * 100
                # print df_current.to_string(line_width=1000)

            print 'df_others length: %d' % len(self.df_others0)

            df_others = pd.concat(data)
            """:type: pd.DataFrame"""
            df_others = df_others.sort_values('date', ascending=False)

            self.df_others1 = df_others

    def continue_split_others(self):
        """
        Run both others and split continue normal using date descending
        """
        print '=' * 130
        print output % ('FIELD', 'Continue old format split/others data', '')
        print '=' * 130

        print 'df_normal length: %d' % len(self.df_normal)
        print 'df_split1 length: %d' % len(self.df_split1)
        print 'df_others1 length: %d' % len(self.df_others1)
        print '-' * 100

        df_date0 = pd.DataFrame()
        if len(self.df_split1):
            group0 = self.df_split1.groupby('option_code')
            dates0 = group0['date'].min()
            df_date0 = pd.DataFrame(dates0)
            df_date0['event'] = 'split'

        df_date1 = pd.DataFrame()
        if len(self.df_others1):
            group1 = self.df_others1.groupby('option_code')
            dates1 = group1['date'].min()
            df_date1 = pd.DataFrame(dates1)
            df_date1['event'] = 'others'

        df_date = pd.concat([df_date0, df_date1])
        """:type: pd.DataFrame"""
        dates = df_date.sort_values('date')

        split_data = []
        others_data = []
        for code, row in dates.iterrows():
            print output % ('FOR', 'code: %s date: %s' % (code, row['date'].strftime('%Y-%m-%d')),
                            'Event: %s' % row['event'])

            if row['event'] == 'split':
                df_current = self.df_split1.query('option_code == %r' % code)
                self.df_split1 = self.df_split1[~self.df_split1.index.isin(df_current.index)]
            elif row['event'] == 'others':
                df_current = self.df_others1.query('option_code == %r' % code)
                self.df_others1 = self.df_others1[~self.df_others1.index.isin(df_current.index)]
            else:
                raise LookupError('Invalid event name: %s' % row['event'])

            print output % (row['event'].upper(), 'Total length:', len(df_current))

            index = df_current.query('date == %r' % row['date'])['index'].iloc[0]

            print output % ('NORMAL', 'Get normal row using', 'index: %s' % index)
            oldest = df_current['date'].iloc[-1]
            df_continue = self.df_normal.query('index == %r & date < %r' % (index, oldest))
            # print df_continue.to_string(line_width=1000)
            if len(df_continue) == len(df_continue['date'].unique()):
                print output % ('NORMAL', 'Merge normal continue option data', len(df_continue))
                df_current = pd.concat([df_current, df_continue])

                # remove data in df_normal
                print output % ('REMOVE', 'old data in df_normal removed', '')
                self.df_normal = self.df_normal[
                    ~self.df_normal.index.isin(df_continue.index)
                ]
            else:
                print output % ('NORMAL', 'Found normal but duplicate date', len(df_continue))

            # update option_code
            df_current['option_code'] = df_current['option_code'].iloc[0]
            # df_current['right'] = df_current['right'].iloc[0]
            # df_current['others'] = df_current['others'].iloc[0]
            print output % ('CODE', 'using option_code:', df_current['option_code'].iloc[0])
            # print output % ('TOTAL', 'final df_current length:', len(df_current))

            # add into data
            if row['event'] == 'split':
                split_data.append(df_current)
            else:
                others_data.append(df_current)
            print '-' * 100

        # save back into df

        if len(split_data):
            df_split1 = pd.concat(split_data)
            """:type: pd.DataFrame"""
            df_split1 = df_split1.sort_values('date', ascending=False)
            self.df_split1 = df_split1

        if len(others_data):
            df_others1 = pd.concat(others_data)
            """:type: pd.DataFrame"""
            df_others1 = df_others1.sort_values('date', ascending=False)
            self.df_others1 = df_others1

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
        print '=' * 130
        print output % ('FIELD', 'Merge new format split data', '')
        print '=' * 130
        print output % ('DATA', 'df_normal length:', len(self.df_normal))

        split_history = SplitHistory.objects.filter(
            Q(symbol=self.symbol.upper()) & Q(date__gte='2013-01-01')
        )
        """:type: pd.DataFrame"""
        print output % ('SPLIT', 'Split history in db: %d' % len(split_history), split_history)
        print '-' * 100

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

                print '-' * 100

        if len(data):
            print output % ('DONE', 'All split data is merge', 'total code: %d' % len(data))
            # merge df_split
            df_split = pd.concat(data)
            """:type: pd.DataFrame"""

            self.df_split2 = df_split

            self.df_normal = self.df_normal[~self.df_normal.index.isin(df_split.index)]
            print output % ('REMOVE', 'old data in df_normal removed', '')
            print output % ('DATA', 'df_normal length:', len(self.df_normal))
        else:
            print output % ('EMPTY', 'No new split data for', self.symbol)

    def format_normal_code(self):
        """
        Format option code for DataFrame
        :return: pd.DataFrame
        """
        if not len(self.df_normal):
            return

        # print df.head().to_string(line_width=1000)
        df_format = self.df_normal.sort_values('date', ascending=False).copy()

        group = df_format.groupby('index2')
        unique = group['option_code'].unique().apply(lambda x: len(x))

        data = []
        for index, _ in unique[unique > 1].iteritems():
            df_current = df_format.query('%s == %r' % ('index2', index)).copy()
            contract = get_contract(df_current)
            new_code = check_code(self.symbol, contract)

            df_current['option_code'] = new_code
            data.append(df_current)

            print output % ('CODE', 'Set unique code:', new_code)

        if len(data):
            df_update = pd.concat(data)
            """:type: pd.DataFrame"""

            df_format = df_format[~df_format.index.isin(df_update.index)]
            df_format = pd.concat([df_format, df_update])

        # assert len(df_format) == len(df)
        print output % ('STAT', 'Old rows: %d' % len(self.df_normal),
                        'Format rows: %d' % len(df_format))

        self.df_normal = df_format.copy()

    def start(self):
        """
        Start extract all option from raw csv data
        """
        # main functions
        self.get_data()
        self.group_data()
        self.merge_old_split_data()
        self.merge_others_data()
        self.merge_new_split_data()

        # format codes
        self.format_normal_code()

        # re_index
        self.df_normal = self.df_normal.reset_index(drop=True)
        self.df_others1 = self.df_others1.reset_index(drop=True)
        self.df_split1 = self.df_split1.reset_index(drop=True)
        self.df_split2 = self.df_split2.reset_index(drop=True)

        print '=' * 130
        print output % ('FIELD', 'Complete extract option data', '')
        print '=' * 130
        print output % ('STAT', 'df_normal length: %d' % len(self.df_normal), '')
        print output % ('STAT', 'df_others length: %d' % len(self.df_others1), '')
        print output % ('STAT', 'df_split1 length: %d' % len(self.df_split1), '')
        print output % ('STAT', 'df_split2 length: %d' % len(self.df_split2), '')

        db = pd.HDFStore(QUOTE)

        try:
            db.remove('option/%s/raw' % self.symbol.lower())
        except KeyError:
            pass
        db.append('option/%s/raw/normal' % self.symbol.lower(), self.df_normal)
        db.append('option/%s/raw/others' % self.symbol.lower(), self.df_others1)
        db.append('option/%s/raw/split/old' % self.symbol.lower(), self.df_split1)
        db.append('option/%s/raw/split/new' % self.symbol.lower(), self.df_split2)
        db.close()

        print output % ('SAVE', 'All data saved', '')


def raw_option_h5(request, symbol):
    """
    Extract then import raw csv data into h5 db
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Start cli for create_raw: %s' % symbol)
    os.system("start cmd /k python data/cli/manage.py create_raw --symbol=%s" % symbol)

    return redirect('admin:data_underlying_changelist')
