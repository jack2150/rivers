import logging
import os
import pandas as pd
from HTMLParser import HTMLParser
from glob import glob
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from shutil import rmtree
from data.models import Underlying
from rivers.settings import QUOTE, BASE_DIR


logger = logging.getLogger('views')


def import_earning(lines, symbol):
    """
    open read fidelity earning file
    :param lines: list of str
    :param symbol: str
    :return: None
    """
    l = [l for l in lines if 'Estimates by Fiscal Quarter' in l][0]
    l = l[l.find('<tbody>') + 7:l.find('</tbody>')]

    # noinspection PyAbstractClass
    class EarningParser(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)

            self.after_smart_estimate = False
            self.data = list()

            self.temp = list()
            self.start = False

        def handle_data(self, data):
            if self.after_smart_estimate:
                if data.split(' ')[0] in ('Q1', 'Q2', 'Q3', 'Q4'):
                    self.start = True

                if self.start:
                    self.temp.append(data)

                if len(self.temp) == 10:
                    if self.temp[5] and self.temp[9]:
                        self.temp[9] = self.temp[5]

                    if '--' not in self.temp:
                        self.data.append(self.temp)

                    self.temp = list()
                    self.start = False

            if data == 'SmartEstimate':
                self.after_smart_estimate = True

    p = EarningParser()
    p.feed(l)
    # update and add new
    earnings = list()
    for l in p.data:
        # print l
        e = {k: str(v) for k, v in zip(
            ['report_date', 'actual_date', 'release', 'estimate_eps', 'analysts',
             'adjusted_eps', 'diff', 'hl', 'gaap', 'actual_eps'], l
        )}

        e['quarter'] = e['report_date'].split(' ')[0]
        e['year'] = int(e['report_date'].split(' ')[1])
        e['actual_date'] = pd.datetime.strptime(e['actual_date'], '%m/%d/%y')  # .date()
        e['analysts'] = int(e['analysts'][1:-1].replace(' Analysts', ''))
        e['low'] = float(e['hl'].split(' / ')[0])
        e['high'] = float(e['hl'].split(' / ')[1])
        del e['report_date'], e['hl'], e['diff']

        for key in ('estimate_eps', 'adjusted_eps', 'gaap', 'actual_eps'):
            e[key] = float(e[key])

        earnings.append(e)
    if len(earnings):
        db = pd.HDFStore(QUOTE)

        try:
            db.remove('event/earning/%s' % symbol.lower())
        except KeyError:
            pass

        df_earning = pd.DataFrame(earnings, index=range(len(earnings)))
        # print df_earning
        db.append(
            'event/earning/%s' % symbol.lower(), df_earning,
            format='table', data_columns=True, min_itemsize=100
        )
        db.close()

        # update earning
        underlying = Underlying.objects.get(symbol=symbol.upper())
        underlying.log += 'Earnings event imported, length: %d\n' % len(df_earning)
        underlying.save()


def import_dividend(lines, symbol):
    l = [l for l in lines if 'Dividends by Calendar Quarter of Ex-Dividend Date' in l][0]
    l = l[l.find('<tbody>') + 7:l.find('</tbody>')]

    # noinspection PyAbstractClass
    class DividendParser(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)

            self.after_smart_estimate = False
            self.data = list()

            self.temp = list()
            self.counter = 0

        def handle_data(self, data):
            self.temp.append(data)
            if self.counter < 7:
                self.counter += 1
            else:
                self.data.append(self.temp)
                self.temp = list()
                self.counter = 0

    p = DividendParser()
    p.feed(l)
    dividends = list()
    for l in p.data:
        d = {k: str(v) for k, v in zip(
            ['year', 'quarter', 'announce_date', 'expire_date',
             'record_date', 'payable_date', 'amount', 'dividend_type'], l
        )}

        for date in ('announce_date', 'expire_date', 'record_date', 'payable_date'):
            d[date] = pd.datetime.strptime(d[date], '%m/%d/%Y')

        d['year'] = int(d['year'])
        d['amount'] = float(d['amount'])

        dividends.append(d)
    if len(dividends):
        db = pd.HDFStore(QUOTE)

        try:
            db.remove('event/dividend/%s' % symbol.lower())
        except KeyError:
            pass

        df_dividend = pd.DataFrame(dividends, index=range(len(dividends)))
        # print df_dividend
        db.append(
            'event/dividend/%s' % symbol.lower(), df_dividend,
            format='table', data_columns=True, min_itemsize=100
        )
        db.close()

        # update dividend
        underlying = Underlying.objects.get(symbol=symbol.upper())
        underlying.log += 'Dividends event imported, length: %d\n' % len(df_dividend)
        underlying.save()


def group_event_files():
    """
    Move files from fidelity __raw__ folder into earnings and dividends folder
    :return: None
    """
    # noinspection PyUnresolvedReferences
    files = glob(os.path.join(BASE_DIR, 'files', 'fidelity', '__raw__', '*.html'))
    # noinspection PyUnresolvedReferences
    earning_path = os.path.join(BASE_DIR, 'files', 'fidelity', 'earnings')
    # noinspection PyUnresolvedReferences
    dividend_path = os.path.join(BASE_DIR, 'files', 'fidelity', 'dividends')

    for f0 in files:
        fname = os.path.basename(f0)
        if 'Earnings' in f0:
            f1 = os.path.join(earning_path, fname)
        else:
            f1 = os.path.join(dividend_path, fname)

        if os.path.isfile(f1):
            os.remove(f1)

        os.rename(f0, f1)
    else:
        # noinspection PyUnresolvedReferences
        rmtree(os.path.join(BASE_DIR, 'files', 'fidelity', '__raw__'), ignore_errors=True)
        # noinspection PyUnresolvedReferences
        os.mkdir(os.path.join(BASE_DIR, 'files', 'fidelity', '__raw__'))


def html_event_import(request, symbol):
    """
    HTML event import without using form
    :param request: request
    :param symbol: str
    :return: return
    """
    logger.info('Import html event: %s' % symbol)
    group_event_files()

    symbol = symbol.upper()
    # noinspection PyUnresolvedReferences
    earning_lines = open(os.path.join(
        BASE_DIR, 'files', 'fidelity', 'earnings', '%s _ Earnings - Fidelity.html' % symbol)
    ).readlines()
    import_earning(earning_lines, symbol)
    logger.info('Complete import earnings')

    try:
        # noinspection PyUnresolvedReferences
        dividend_lines = open(os.path.join(
            BASE_DIR, 'files', 'fidelity', 'dividends', '%s _ Dividends - Fidelity.html' % symbol)
        ).readlines()
        import_dividend(dividend_lines, symbol)
        logger.info('Complete import dividends')
    except IOError:
        logger.info('No dividend data')

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))