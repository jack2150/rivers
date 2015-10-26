from HTMLParser import HTMLParser
import calendar
from glob import glob
import os
import re
import urllib2
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import render, redirect
from pandas.io.data import get_data_google, get_data_yahoo
from data.extra import offday, holiday
from data.models import Underlying, Treasury
from data.plugin.thinkback import ThinkBack
from rivers.settings import QUOTE, BASE_DIR
import numpy as np
import pandas as pd


def get_dte_date(ex_month, ex_year):
    """
    Use option contract ex_month and ex_year to get dte date
    :param ex_month: str
    :param ex_year: int
    :return: date
    """
    year = pd.datetime.strptime(str('%02d' % ex_year), '%y').year
    calendar.setfirstweekday(calendar.SUNDAY)
    month_abbr = [calendar.month_abbr[i].upper() for i in range(1, 13)]

    if len(ex_month) == 4:
        # not 3th week
        month = month_abbr.index(ex_month[:3]) + 1
        week = int(ex_month[3:])
    else:
        # standard 3th week
        month = month_abbr.index(ex_month[:3]) + 1
        week = 3

    # every week need trading day as whole
    c = calendar.monthcalendar(ex_year, month)
    for w in c:
        if not any(w[1:6]):
            del c[c.index(w)]

    # get day in calendar
    day = c[week - 1][-2]
    if day == 0:
        day = [d for d in c[week - 1] if d != 0][-1]

    return pd.Timestamp('%04d%02d%02d' % (year, month, day)).date()


def get_exist_stocks(symbol):
    """
    get symbol dataframe from quote db
    :param symbol:
    :return: DataFrame
    """
    db = pd.HDFStore(QUOTE)
    try:
        df_stock = db.select('stock/thinkback/%s' % symbol.lower())
    except KeyError:
        df_stock = pd.DataFrame({})
    db.close()

    return df_stock


def code2key(option_code):
    """
    Replace option code into hdf5 table key
    :param option_code: str
    :return: str
    """
    return str(option_code).replace('.', '_')


def csv_stock_h5(request, symbol):
    """
    Import csv files stock data only
    /stock/gld
    :param request: request
    :param symbol: str
    :return: render
    """
    symbol = symbol.lower()

    # remove all
    db = pd.HDFStore(QUOTE)
    try:
        db.remove('stock/thinkback/%s' % symbol.lower())
    except KeyError:
        pass
    db.close()

    # get underlying
    underlying = Underlying.objects.get(symbol=symbol.upper())
    start = underlying.start
    end = underlying.stop

    # move files into year folder
    path = os.path.join(BASE_DIR, 'files', 'thinkback', symbol)
    no_year_files = glob(os.path.join(path, '*.csv'))
    years = sorted(list(set([
        os.path.basename(f)[:4] for f in no_year_files
    ])))

    for year in years:
        year_dir = os.path.join(path, year)

        # make dir if not exists
        if not os.path.isdir(year_dir):
            os.mkdir(year_dir)

        # move all year files into dir
        for no_year_file in no_year_files:
            filename = os.path.basename(no_year_file)
            if filename[:4] == year:
                try:
                    os.rename(no_year_file, os.path.join(year_dir, filename))
                except WindowsError:
                    # remove old file, use new file
                    os.remove(os.path.join(year_dir, filename))
                    os.rename(no_year_file, os.path.join(year_dir, filename))
                    pass

    # only get valid date
    trading_dates = pd.Series([d.date() for d in pd.bdate_range(start, end)])
    trading_dates = np.array(
        trading_dates[
            trading_dates.apply(lambda x: not offday(x) and not holiday(x))
        ].apply(lambda x: x.strftime('%Y-%m-%d'))
    )

    files = []
    for year in glob(os.path.join(path, '*')):
        for csv in glob(os.path.join(year, '*.csv')):
            # skip date if not within underlying dates
            if os.path.basename(csv)[:10] in trading_dates:
                files.append(csv)

    # open db
    df_exist = get_exist_stocks(symbol)

    # start save csv
    error_dates = list()
    stocks = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}
    for i, f in enumerate(sorted(files)):
        # get date and symbol
        fdate, _ = os.path.basename(f)[:-4].split('-StockAndOptionQuoteFor')

        # check exists
        date = pd.datetime.strptime(fdate, '%Y-%m-%d')
        if date in df_exist.index:
            continue  # skip

        #if start > date.date() or date.date() > end:
        #    continue  # skip not within underlying date

        bday = pd.datetime.strptime(fdate, '%Y-%m-%d').date()
        trading_day = not (holiday(bday) or offday(bday))

        if trading_day:
            # output to console
            print '%-05d %-20s' % (i, os.path.basename(f))

            stock_data, option_data = ThinkBack(f).read()

            try:
                if int(stock_data['volume']) == 0:
                    error_dates.append(fdate)
                    continue  # skip this part
            except ValueError:
                continue

            # save stock
            stocks['date'].append(pd.datetime.strptime(stock_data['date'], '%Y-%m-%d'))
            stocks['open'].append(np.float64(stock_data['open']))
            stocks['high'].append(np.float64(stock_data['high']))
            stocks['low'].append(np.float64(stock_data['low']))
            stocks['close'].append(np.float64(stock_data['last']))
            stocks['volume'].append(np.int64(stock_data['volume']))
    else:
        df_stock = pd.DataFrame(stocks)

        if len(df_stock):
            df_stock = df_stock.set_index('date')

            quote = pd.HDFStore(QUOTE)
            quote.append('stock/thinkback/%s' % symbol, df_stock,
                         format='table', data_columns=True)
            quote.close()

    # check missing dates
    df_exist = get_exist_stocks(symbol)

    missing = list()
    bdays = pd.bdate_range(start=start, end=end, freq='B')
    for bday in bdays:
        if holiday(bday.date()) or offday(bday.date()):
            continue

        if not bday in df_exist.index:
            missing.append(bday.date())

    # update underlying
    underlying.thinkback = len(df_exist)
    underlying.missing = missing
    underlying.save()

    # stats
    stats = {'count': len(df_stock), 'start': start, 'stop': end}

    completes = [{'date': i.strftime('%Y-%m-%d'), 'volume': v['volume'], 'close': round(v['close'], 2)}
                 for i, v in df_stock.iterrows()]

    #os.remove(QUOTE)

    # view
    template = 'data/csv_stock_h5.html'

    parameters = dict(
        site_title='Csv Stock import',
        title='Thinkback csv stock import: {symbol}'.format(symbol=symbol.upper()),
        symbol=symbol,
        stats=stats,
        completes=completes,
        missing=missing
    )

    return render(request, template, parameters)


def csv_option_h5(request, symbol):
    """
    Import thinkback csv options into db,
    every time this run, it will start from first date

    /option/gld/date -> keep all inserted date
    /option/gld/contract -> GLD150117C114 data
    /option/gld/code/GLD7150102C110 -> values

    how do you get daily all delta > 0.5 option?

    :param request: request
    :param symbol: str
    :return: render
    """
    symbol = symbol.lower()
    path = os.path.join(BASE_DIR, 'files', 'thinkback', symbol)

    #stocks = Stock.objects.filter(Q(symbol=symbol) & Q(source='thinkback')).order_by('date')

    df_stock = get_exist_stocks(symbol)
    #print df_stock

    # open db
    db = pd.HDFStore(QUOTE)

    # remove all existing data
    for key in ('date', 'index', 'contract', 'data'):
        try:
            db.remove('option/%s/%s' % (symbol, key))
        except KeyError:
            pass

    # all new
    df_contract = pd.DataFrame(columns=[
        'option_code',
        'ex_date', 'ex_month', 'ex_year', 'expire',
        'name', 'others', 'right', 'special', 'strike'
    ])
    dc_index = {}
    options = {}

    # start loop every date
    inserted = 0
    for index, values in df_stock.iterrows():
        # open path get option data
        year = index.date().strftime('%Y')
        fpath = os.path.join(
            path, year, '%s-StockAndOptionQuoteFor%s.csv' % (
                index.date().strftime('%Y-%m-%d'), symbol.upper()
            )
        )
        _, option_data = ThinkBack(fpath).read()

        # get all contract
        contracts = [c for c, _ in option_data]

        # date code index
        if len(contracts):
            for c in contracts:
                if c['option_code'] in dc_index.keys():
                    dc_index[c['option_code']].append(index)
                else:
                    dc_index[c['option_code']] = [index]

        print 'D | %-12s | ' % index.strftime('%Y-%m-%d'), 'CONTRACT: %-7s | ' % len(contracts),
        print 'INDEX LENGTH: %-10s | ' % len(dc_index.keys()),

        # get new contract and a list of no list code
        option_code = np.array(df_contract[False == df_contract['expire']]['option_code'])
        df_remain = df_contract[False == df_contract['expire']]  # get no expire contract

        new_contract = []
        for c in contracts:
            if c['option_code'] in option_code:
                if len(df_remain):
                    df_remain = df_remain[df_remain['option_code'] != c['option_code']]
                continue

            c['ex_date'] = pd.Timestamp(get_dte_date(c['ex_month'], int(c['ex_year'])))
            c['expire'] = 0

            new_contract.append(c)

        p = True
        if len(df_remain):
            for n in [n for n in new_contract]:
                #new is not in option code, so we need to check spec is same
                update = 0
                code0 = ''
                code1 = n['option_code']
                query = [
                    'name == %r' % n['name'],
                    'ex_month == %r' % n['ex_month'],
                    'ex_year == %r' % n['ex_year'],
                    'special == %r' % n['special'],
                    'strike == %r' % n['strike'],
                    'right == %r' % n['right'],
                    'others == %r' % n['others']
                ]

                # full found on everything is same
                found0 = df_remain.query(' & '.join(query))
                if len(found0) == 1:
                    #print n['option_code'], 'found full'
                    update = 1
                    code0 = found0['option_code'][found0.index.values[0]]
                elif len(found0) > 1:
                    print found0
                    raise LookupError('%s found %d similar full specs' % (n['option_code'], len(found0)))

                # got others, special div, announcement
                found1 = df_remain.query(' & '.join(query[:-1]))  # without others
                if not update and len(found1) == 1:
                    #print n['option_code'], 'found without others full'
                    update = 2
                    code0 = found1['option_code'][found1.index.values[0]]
                elif len(found1) > 1:
                    print found1
                    raise LookupError('%s found %d others specs' % (n['option_code'], len(found1)))

                # got split or bonus issue or etc...
                found2 = df_remain.query(' & '.join(query[:-2]))  # without others and right
                if not update and len(found2) == 1:
                    #print n['option_code'], 'found without others full'
                    update = 3
                    code0 = found2['option_code'][found2.index.values[0]]
                elif len(found2) > 2:
                    print found2
                    raise LookupError('%s found %d others right specs' % (n['option_code'], len(found2)))

                if update:
                    if p:
                        print ''
                        p = False

                    print 'C | %-12s | %-27s | %-14s => %-14s' % (
                        'CODE CHANGE',
                        [
                            '',
                            'NORMAL (Old to new format)',
                            'OTHERS (Special dividend or etc)',
                            'RIGHT (Split, bonus issue or etc)',
                        ][update],
                        code0,
                        code1
                    )

                    # remove code from df_remain
                    df_remain = df_remain[df_remain['option_code'] != code0]

                    # remove contract code from df_contract
                    df_contract.loc[df_contract['option_code'] == code0, 'option_code'] = code1
                    # update all
                    df_contract.loc[df_contract['option_code'] == code1, 'others'] = n['others']
                    df_contract.loc[df_contract['option_code'] == code1, 'right'] = n['right']

                    # update option data from old key name into new key name
                    options[code1] = []
                    if code0 in options.keys():
                        options[code1] += options[code0]
                        del options[code0]  # remove option data in new data

                    # update date code index
                    dc_index[code1] = []
                    if code0 in options.keys():
                        dc_index[code1] += dc_index[code0]
                        del dc_index[code0]  # remove option data in new data

                    # remove from new contract list
                    del new_contract[new_contract.index(n)]

        if len(df_remain):
            #print df_remain.to_string(line_width=600)
            print 'MISSING: %-6d | ' % len(df_remain),
            print 'ACTIVE: %-6d' % len(df_contract[False == df_contract['expire']])

            for _, c in df_remain.iterrows():
                q = df_contract['option_code'] == c['option_code']
                df_contract.loc[q, 'missing'] += 1

        else:
            print 'NO MISSING        | ',
            print 'ACTIVE: %-6d' % len(df_contract[False == df_contract['expire']])

        # insert new contract into df_contract
        if len(new_contract):
            # find existing expire option code and replace old code
            if len(df_contract):
                option_code = np.array(df_contract[df_contract['expire']]['option_code'])
                for c in new_contract:
                    if c['option_code'] in option_code:  # exist in expire code
                        try:
                            strike = '%d' % int(c['strike'])
                        except ValueError:
                            strike = '%f' % float(c['strike'])

                        new_code = '{symbol}{year}{month}{day}{name}{strike}'.format(
                            symbol=symbol.upper(),
                            year=c['ex_date'].date().strftime('%y'),
                            month=c['ex_date'].date().strftime('%m'),
                            day=c['ex_date'].date().strftime('%d'),
                            name=c['name'][0].upper(),
                            strike=strike
                        )
                        print 'C | CODE UPDATE  | %-27s | %-14s => %-14s' % (
                            'OLD UPDATE INTO NEW FORMAT', c['option_code'], new_code
                        )

                        # change old code, not new code
                        q = df_contract['option_code'] == c['option_code']
                        df_contract.loc[q, 'option_code'] = new_code

            # add new contract into df_contract
            df = pd.DataFrame(new_contract)
            df['expire'] = df['expire'].astype('bool')
            df['missing'] = 0
            if len(df_contract):
                df_contract = pd.concat([df_contract, df])
            else:
                df_contract = df

        # insert option into big option data list
        for c, o in option_data:
            o['date'] = index
            o['option_code'] = c['option_code']

            if c['option_code'] in options.keys():
                if float(o['bid']) >= float(o['ask']):
                    continue  # bid must less than ask price

                if float(o['bid']) > 0 or float(o['ask']) > 0:  # only bid or ask > 0
                    options[c['option_code']].append(o)
            else:
                options[c['option_code']] = [o]

        # expire, save into db and delete from new and old
        q0 = df_contract['ex_date'] <= index
        q1 = False == df_contract['expire']
        if np.any(q0 & q1):
            ex_data = []
            for _, c in df_contract[q0 & q1].iterrows():
                inserted += 1
                ex_data += options[c['option_code']]

                print 'E | OPTION %-5d | %-30s | %-20s | %-6d' % (
                    inserted,
                    'EXPIRE & INSERT OPTION CODE',
                    c['option_code'],
                    len(options[c['option_code']])
                )
                del options[c['option_code']]

            df_expire = pd.DataFrame(ex_data, index=range(len(ex_data))).set_index('date')
            db.append(
                'option/%s/data' % symbol, df_expire,
                format='table', data_columns=True, min_itemsize=100
            )

            # set all expire
            df_contract.loc[df_contract['ex_date'] <= index, 'expire'] = 1

    df_index = pd.DataFrame()
    if len(dc_index.keys()):
        dc_data = []
        for code, dates in dc_index.items():
            for d in dates:
                dc_data.append({
                    'date': d,
                    'option_code': code
                })

        df_index = pd.DataFrame(dc_data, index=range(len(dc_data))).set_index('date')
        db.append(
            'option/%s/index' % symbol, df_index,
            format='table', data_columns=True, min_itemsize=100
        )

    if len(df_contract):
        db.append(
            'option/%s/contract' % symbol, df_contract,
            format='table', data_columns=True, min_itemsize=100
        )

    if len(options):
        # finish, insert all new_data
        data = []
        for k, l in options.items():
            inserted += 1
            for v in l:
                data.append(v)
            del options[k]  # remove in options

            print 'I | OPTION %-5d | INSERT OPTION CODE: %-20s | LENGTH: %-5s' % (inserted, k, len(l))

        df_data = pd.DataFrame(data, index=range(len(data))).set_index('date')
        db.append(
            'option/%s/data' % symbol, df_data,
            format='table', data_columns=True, min_itemsize=100
        )

    missing = []
    df_missing = db.select('option/%s/contract' % symbol, 'missing > 0')
    if len(df_missing):
        for _, m in df_missing.sort(['missing'], ascending=[False]).iterrows():
            missing.append({
                'option_code': m['option_code'],
                'count': m['missing']
            })

    completed = []
    if len(df_index):
        for i in df_index.index.unique():
            completed.append({
                'date': i.date(),
                'count': len(df_index.ix[i]),
            })

    df_data = db.select('option/%s/data' % symbol)
    df_contract = db.select('option/%s/contract' % symbol)
    stats = {
        'data': len(df_data),
        'index': len(df_index),
        'contract': len(df_contract),
        'expire': len(df_contract[df_contract['expire']]),
        'active': len(df_contract[False == df_contract['expire']]),
        'right': ', '.join(df_contract['right'].unique()),
        'others': ', '.join(df_contract[df_contract['others'] != '']['others'].unique()),
        'special': ', '.join(df_contract['special'].unique())
    }

    # close db
    db.close()

    # update underlying
    underlying = Underlying.objects.get(symbol=symbol.upper())
    underlying.contract = len(df_contract)
    underlying.option = len(df_data)
    underlying.save()

    template = 'data/csv_option_h5.html'
    parameters = dict(
        site_title='Csv option import',
        title='Thinkback csv option import: {symbol}'.format(symbol=symbol.upper()),
        symbol=symbol.upper(),
        stats=stats,
        missing=missing,
        completed=completed
    )

    return render(request, template, parameters)


def web_stock_h5(request, source, symbol):
    """
    Web import into hdf5 db
    :param source: str
    :param request: request
    :param symbol: str
    :return: render
    """
    symbol = symbol.upper()

    # get underlying
    underlying = Underlying.objects.get(symbol=symbol)
    start = underlying.start
    end = underlying.stop

    # get data function and get data
    f = get_data_google if source == 'google' else get_data_yahoo
    df_stock = f(symbols=symbol, start=start, end=end)

    # drop if ohlc is empty
    for field in ['Open', 'High', 'Low', 'Close']:
        df_stock[field] = df_stock[field].replace('-', np.nan).astype(float)

    # do not drop if volume is empty
    df_stock['Volume'] = df_stock['Volume'].replace('-', 0).astype(long)

    # rename into lower case
    df_stock.columns = [c.lower() for c in df_stock.columns]

    if source == 'yahoo':
        del df_stock['adj close']

    # skip or insert
    db = pd.HDFStore(QUOTE)
    if len(df_stock):
        try:
            db.remove('stock/%s/%s' % (source, symbol.lower()))  # remove old
        except KeyError:
            pass
        db.append(
            'stock/%s/%s' % (source, symbol.lower()), df_stock,
            format='table', data_columns=True, min_itemsize=100
        )  # insert new
    db.close()

    # update symbol stat
    if source == 'google':
        underlying.google = len(df_stock)
    else:
        underlying.yahoo = len(df_stock)

    underlying.save()

    # stocks
    stocks = []
    for i, s in df_stock[::-1].iterrows():
        stocks.append('%-16s | %20.2f | %20.2f | %20.2f | %20.2f | %20d' % (
            i.date(), s['open'], s['high'], s['low'], s['close'], s['volume']
        ))

    # for testing
    # Stock.objects.all().delete()
    template = 'data/web_stock_h5.html'
    parameters = dict(
        site_title='Web import',
        title='{source} Web import: {symbol}'.format(
            source=source.capitalize(), symbol=symbol
        ),
        symbol=symbol.lower(),
        source=source,
        stocks=stocks
    )

    return render(request, template, parameters)


class TreasuryForm(forms.Form):
    url = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={'class': 'form-control vTextField'})
    )


def web_treasury_h5(request):
    """
    Web import treasury data int db and h5
    :param request: request
    :return: render
    """
    if request.method == 'POST':
        form = TreasuryForm(request.POST)
        if form.is_valid():
            response = urllib2.urlopen(form.cleaned_data['url'])
            html = response.readlines()
            #html = open(r'C:\Users\Jack\Downloads\FRB_H15 (1).csv').readlines()

            if len(html) < 6:
                raise LookupError('Unable connect to internet or link is invalid')

            data0 = {}
            for i in range(6):
                raw = re.split('(\d+|\w[-.,_:/ A-Za-z0-9]+)', html[i].strip())
                name = raw[1].strip().replace(' ', '_').replace(':', '').lower()

                data0[name] = raw[3]
                if name == 'multiplier':
                    data0[name] = float(raw[3])
                print name

            # remove old treasury
            try:
                Treasury.objects.get(time_period=data0['time_period']).delete()
            except ObjectDoesNotExist:
                pass

            # create new treasury
            treasury = Treasury(**data0)

            rate = {'date': [], 'rate': []}
            for i in range(6, len(html)):
                raw = html[i].strip().split(',')
                rate['date'].append(pd.datetime.strptime(raw[0], '%Y-%m-%d'))
                if raw[1] == 'ND':
                    rate['rate'].append(np.nan)
                else:
                    rate['rate'].append(float(raw[1]))

            df_rate = pd.DataFrame(rate).set_index('date').fillna(method='pad')

            db = pd.HDFStore(QUOTE)
            # remove old treasury data
            try:
                db.remove('treasury/%s' % treasury.to_key())
            except KeyError:
                pass
            # append new treasury data
            db.append(
                'treasury/%s' % treasury.to_key(), df_rate,
                format='table', data_columns=True, min_itemsize=100
            )
            db.close()

            treasury.start_date = rate['date'][0]
            treasury.stop_date = rate['date'][-1]

            treasury.save()

            return redirect('admin:data_treasury_changelist')
    else:
        form = TreasuryForm()

    template = 'data/html_treasury_import.html'
    parameters = dict(
        site_title='Treasury import',
        title='Treasury import',
        form=form
    )

    return render(request, template, parameters)


def set_underlying(request, symbol, action):
    """
    Set underlying is updated after import stock
    :param request: request
    :param symbol: str
    :return: redirect
    """
    symbol = symbol.upper()

    underlying = Underlying.objects.get(symbol=symbol)
    if action == 'updated':
        underlying.updated = True
    elif action == 'optionable':
        underlying.optionable = True
    else:
        raise ValueError('Invalid view action')
    underlying.save()

    return redirect(reverse('admin:data_underlying_changelist'))


class EventImportForm(forms.Form):
    symbol = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control vTextField'})
    )
    event = forms.CharField(
        max_length=20,
        widget=forms.HiddenInput()
    )
    fidelity_file = forms.FileField()

    def clean(self):
        """
        Validate file name before start insert
        """
        cleaned_data = super(EventImportForm, self).clean()
        symbol = cleaned_data.get('symbol')
        event = cleaned_data.get('event')
        fidelity_file = cleaned_data.get('fidelity_file')

        if fidelity_file is None:
            self._errors['fidelity_file'] = self.error_class(
                ['Please select file to import']
            )
        else:
            # event is correct and fname is correct too
            if event == 'earning':
                if ' _ Earnings - Fidelity' not in fidelity_file.__str__():
                    self._errors['fidelity_file'] = self.error_class(
                        ['Invalid fidelity earning file: {f}'.format(f=fidelity_file)]
                    )
            elif event == 'dividend':
                if ' _ Dividends - Fidelity' not in fidelity_file.__str__():
                    self._errors['fidelity_file'] = self.error_class(
                        ['Invalid fidelity dividend file: {f}'.format(f=fidelity_file)]
                    )
            else:
                self._errors['event'] = self.error_class(
                    ['Invalid event: {event}'.format(event=event)]
                )

            # symbol must be match
            symbol1 = fidelity_file.__str__().split(' _ ')[0]
            if symbol != symbol1:
                self._errors['symbol'] = self.error_class(
                    ['Symbol is not match: {symbol0} != {symbol1}'.format(
                        symbol0=symbol,
                        symbol1=symbol1
                    )]
                )

        return cleaned_data

    def import_earning(self):
        """
        Verify thinkback earning by using fidelity earning data
        including update, create, and delete invalid data
        """
        cleaned_data = super(EventImportForm, self).clean()

        symbol = cleaned_data['symbol']
        f = cleaned_data.get("fidelity_file")

        # open read fidelity file
        lines = f.readlines()
        l = [l for l in lines if 'Estimates by Fiscal Quarter' in l][0]
        l = l[l.find('<tbody>') + 7:l.find('</tbody>')]

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
            #print l
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
            #print df_earning
            db.append(
                'event/earning/%s' % symbol.lower(), df_earning,
                format='table', data_columns=True, min_itemsize=100
            )
            db.close()

            # update earning
            underlying = Underlying.objects.get(symbol=symbol.upper())
            underlying.earning = len(df_earning)
            underlying.save()

    def insert_dividend(self):
        """
        Verify thinkback earning by using fidelity earning data
        including update, create, and delete invalid data
        """
        cleaned_data = super(EventImportForm, self).clean()

        symbol = cleaned_data['symbol']
        f = cleaned_data.get('fidelity_file')

        # open read fidelity file
        lines = f.readlines()
        l = [l for l in lines if 'Dividends by Calendar Quarter of Ex-Dividend Date' in l][0]
        l = l[l.find('<tbody>') + 7:l.find('</tbody>')]

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
            #print df_dividend
            db.append(
                'event/dividend/%s' % symbol.lower(), df_dividend,
                format='table', data_columns=True, min_itemsize=100
            )
            db.close()

            # update dividend
            underlying = Underlying.objects.get(symbol=symbol.upper())
            underlying.dividend = len(df_dividend)
            underlying.save()


def html_event_import(request, event, symbol):
    """
    Verify earning data from thinkback using fidelity data
    :param request: request
    :return: render
    """
    if event in ('earning', 'dividend'):
        if request.method == 'POST':
            form = EventImportForm(request.POST, request.FILES)
            if form.is_valid():
                if event == 'earning':
                    form.import_earning()
                    return redirect('admin:data_underlying_changelist')
                else:
                    form.insert_dividend()
                    return redirect('admin:data_underlying_changelist')
        else:
            form = EventImportForm(
                initial={
                    'symbol': symbol.upper(),
                    'event': event
                }
            )

    else:
        raise Http404("Verify event name not found.")

    template = 'data/html_event_import.html'
    parameters = dict(
        site_title='{event} import'.format(event=event.capitalize()),
        title='{event} import'.format(event=event.capitalize()),
        form=form
    )

    return render(request, template, parameters)


class TruncateSymbolForm(forms.Form):
    symbol = forms.CharField(
        label='Symbol', max_length=20,
        widget=forms.HiddenInput(
            attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
        )
    )


def truncate_symbol(request, symbol):
    """
    Truncate all data for a single symbol
    :param request: request
    :param symbol: str
    :return: render
    """
    symbol = symbol.upper()
    stats = None

    if request.method == 'POST':
        form = TruncateSymbolForm(request.POST)

        if form.is_valid():
            db = pd.HDFStore(QUOTE)

            keys = [
                'stock/thinkback/%s', 'stock/google/%s', 'stock/yahoo/%s',
                'option/%s/contract', 'option/%s/data',
                'event/earning/%s', 'event/dividend/%s',
            ]
            for key in keys:
                try:
                    db.remove(key % symbol.lower())
                except KeyError:
                    pass

            db.close()

            # update underlying
            underlying = Underlying.objects.get(symbol=symbol)
            underlying.thinkback = 0
            underlying.contract = 0
            underlying.option = 0
            underlying.google = 0
            underlying.yahoo = 0
            underlying.earning = 0
            underlying.dividend = 0
            underlying.updated = False
            underlying.optionable = False
            underlying.missing_dates = ''
            underlying.save()

            return redirect(reverse('admin:data_underlying_changelist'))
    else:
        form = TruncateSymbolForm(
            initial={'symbol': symbol}
        )

        db = pd.HDFStore(QUOTE)

        names = ['thinkback', 'google', 'yahoo', 'contract', 'option', 'earning', 'dividend']
        keys = ['stock/thinkback/%s', 'stock/google/%s', 'stock/yahoo/%s',
                'option/%s/contract', 'option/%s/data',
                'event/earning/%s', 'event/dividend/%s']

        df = {}
        for name, key in zip(names, keys):
            try:
                df[name] = db.select(key % symbol.lower())
            except KeyError:
                df[name] = pd.DataFrame()
        db.close()

        stats = {
            'thinkback': {
                'stock': len(df['thinkback']),
                'start': df['thinkback'].index[0].date() if len(df['thinkback']) else 0,
                'stop': df['thinkback'].index[-1].date() if len(df['thinkback']) else 0
            },
            'option': {
                'contract': len(df['contract']),
                'count': len(df['option'])
            },
            'google': {
                'stock': len(df['google']),
                'start': df['google'].index[0].date() if len(df['google']) else 0,
                'stop': df['google'].index[-1].date() if len(df['google']) else 0,
            },
            'yahoo': {
                'stock': len(df['yahoo']),
                'start': df['yahoo'].index[0].date() if len(df['yahoo']) else 0,
                'stop': df['yahoo'].index[-1].date() if len(df['yahoo']) else 0,
            },
            'event': {
                'earning': len(df['earning']),
                'dividend': len(df['dividend']),
            }
        }

    template = 'data/truncate_symbol.html'
    parameters = dict(
        site_title='Truncate symbol',
        title='Truncate symbol',
        symbol=symbol,
        stats=stats,
        form=form
    )

    return render(request, template, parameters)
