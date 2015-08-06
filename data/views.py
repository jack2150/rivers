from HTMLParser import HTMLParser
import codecs
from django import forms
from django.http import Http404
import numpy as np
from pandas.io.data import get_data_google, get_data_yahoo
import calendar
import datetime
from glob import glob
import os
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import render, redirect
from pandas import bdate_range
from data.extra import holiday, offday
from data.models import *
from data.plugin.thinkback import ThinkBack
from rivers.settings import BASE_DIR


def web_quote_import(request, source, symbol):
    """
    Web import quote for a single symbol
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

    s = Stock.objects.filter(
        Q(symbol=symbol) & Q(source=source)
    ).order_by('date')

    # only save after
    try:
        last_date = s.last().date
        start = last_date if last_date > start else start
    except (ObjectDoesNotExist, AttributeError):
        pass

    # get data function and get data
    f = get_data_google if source == 'google' else get_data_yahoo
    data = f(symbols=symbol, start=start, end=end)

    # drop if ohlc is empty
    for field in ['Open', 'High', 'Low', 'Close']:
        data[field] = data[field].replace('-', np.nan).astype(float)

    # do not drop if volume is empty
    data['Volume'] = data['Volume'].replace('-', 0).astype(long)

    # rename into lower case
    data.columns = [c.lower() for c in data.columns]

    # skip or insert
    stocks = list()
    #for line in data.dropna().to_csv().split('\n')[1:-1]:
    for date, row in data.dropna().iterrows():
        try:
            Stock.objects.get(symbol=symbol, source=source, date=date)
        except ObjectDoesNotExist:
            data = dict(row)
            data['date'] = date.strftime('%Y-%m-%d')

            stock = Stock()
            stock.symbol = symbol
            stock.source = source
            stock.load_dict(data)
            stock.save()

            stocks.append(stock)

    # update symbol stat
    if source == 'google':
        underlying.google = Stock.objects.filter(Q(symbol=symbol) & Q(source='google')).count()
    else:
        underlying.yahoo = Stock.objects.filter(Q(symbol=symbol) & Q(source='yahoo')).count()

    underlying.save()

    # for testing
    # Stock.objects.all().delete()
    template = 'data/import_web.html'
    parameters = dict(
        site_title='Web import',
        title='{source} Web import: {symbol}'.format(
            source=source.capitalize(), symbol=symbol
        ),
        symbol=symbol.lower(),
        source=source,
        stocks=stocks[:5] + [None] + stocks[-5:] if len(stocks) > 10 else stocks
    )

    return render(request, template, parameters)


def treasury_import(request):
    """
    Import treasury csv data from
    http://www.federalreserve.gov/releases/h15/data.htm
    :param request: request
    :return: render
    """
    saved = list()
    for root, _, fnames in os.walk(os.path.join(BASE_DIR, 'files', 'treasury')):
        for f in fnames:
            if len(root.split(os.sep)) == 7:
                name, instrument, maturity = root.split(os.sep)[4:]
            else:
                name, maturity = root.split(os.sep)[4:]
                instrument = None

            lines = codecs.open(os.path.join(root, f), encoding="ascii", errors="ignore").readlines()

            try:
                treasury_instrument = TreasuryInstrument.objects.get(
                    unique_identifier=lines[4].rstrip().split('","')[1].replace('"', '')
                )
            except ObjectDoesNotExist:
                treasury_instrument = TreasuryInstrument()
                treasury_instrument.name = name
                treasury_instrument.instrument = instrument
                treasury_instrument.maturity = maturity
                treasury_instrument.time_frame = f[:-4].capitalize()
                treasury_instrument.load_csv(lines[:6])
                treasury_instrument.save()

            exist_dates = [v[0] for v in treasury_instrument.treasuryinterest_set.values_list('date')]

            interests = list()
            for line in lines[6:]:
                treasury_interest = TreasuryInterest()
                treasury_interest.treasury = treasury_instrument
                treasury_interest.load_csv(line)

                if treasury_interest.date not in exist_dates:
                    interests.append(treasury_interest)

            if interests:
                TreasuryInterest.objects.bulk_create(interests)

                saved.append(dict(
                    fname=os.path.join(root, f),
                    treasury=treasury_instrument,
                    interests=len(interests),
                    start=interests[0].date,
                    end=interests[-1].date
                ))

    # when testing
    #TreasuryInstrument.objects.all().delete()

    template = 'data/import_treasury.html'
    parameters = dict(
        site_title='Treasury import',
        title='Treasury import',
        files=saved
    )

    return render(request, template, parameters)


class TruncateSymbolForm(forms.Form):
    symbol = forms.CharField(
        label='Symbol', max_length=20,
        widget=forms.HiddenInput(
            attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
        )
    )

    def truncate_data(self):
        """
        Remove all data for single symbol
        """
        symbol = self.clean()['symbol'].upper()

        # remove both thinkback, google and yahoo stock
        Stock.objects.filter(symbol=symbol).all().delete()

        # remove contract and options
        OptionContract.objects.filter(symbol=symbol).all().delete()


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
            form.truncate_data()

            # update underlying
            underlying = Underlying.objects.get(symbol=symbol)
            underlying.thinkback = 0
            underlying.google = 0
            underlying.yahoo = 0
            underlying.updated = False
            underlying.validated = False
            underlying.missing_dates = ''
            underlying.save()

            return redirect(reverse('admin:data_underlying_changelist'))
    else:
        form = TruncateSymbolForm(
            initial={'symbol': symbol}
        )

        thinkback = Stock.objects.filter(Q(symbol=symbol) & Q(source='thinkback'))
        google = Stock.objects.filter(Q(symbol=symbol) & Q(source='google'))
        yahoo = Stock.objects.filter(Q(symbol=symbol) & Q(source='yahoo'))
        contracts = OptionContract.objects.filter(symbol=symbol)
        options = Option.objects.filter(contract__symbol=symbol)

        stats = {
            'thinkback': {
                'stock': thinkback.count(),
                'start': thinkback[0].date if thinkback.count() else 0,
                'stop': thinkback[thinkback.count() - 1].date if thinkback.count() else 0,
                'contract': contracts.count(),
                'option': options.count()
            },
            'google': {
                'stock': google.count(),
                'start': google[0].date if google.count() else 0,
                'stop': google[google.count() - 1].date if google.count() else 0
            },
            'yahoo': {
                'stock': yahoo.count(),
                'start': yahoo[0].date if yahoo.count() else 0,
                'stop': yahoo[yahoo.count() - 1].date if yahoo.count() else 0
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


def csv_stock_import(request, symbol):
    """
    Import csv files stock data only
    :param request: request
    :param symbol: str
    :return: render
    """
    # get underlying
    underlying = Underlying.objects.get(symbol=symbol.upper())
    start = underlying.start
    end = underlying.stop

    # move files into year folder
    path = os.path.join(BASE_DIR, 'files', 'thinkback', symbol.lower())
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

    # start save csv
    completed_files = list()
    no_data_dates = list()
    stocks = list()
    for i, f in enumerate(sorted(files)):
        # get date and symbol
        fdate, symbol = os.path.basename(f)[:-4].split('-StockAndOptionQuoteFor')

        # check exists
        is_exists = Stock.objects.filter(
            Q(symbol=symbol) & Q(date=fdate) & Q(source='thinkback')
        ).exists()

        bday = datetime.datetime.strptime(fdate, '%Y-%m-%d')
        trading_day = not (holiday(bday) or offday(bday))

        if not is_exists and trading_day:
            # output to console
            print '%05d' % i, 'RUNNING', os.path.basename(f), 'STOCK'

            stock_data, option_data = ThinkBack(f).read()

            try:
                if int(stock_data['volume']) == 0:
                    no_data_dates.append(datetime.datetime.strptime(fdate, '%Y-%m-%d').date())
                    continue  # skip this part
            except ValueError:
                continue

            # save stock
            stock = Stock()
            stock.symbol = symbol
            stock.load_dict(stock_data)
            stock.source = 'thinkback'
            stocks.append(stock)
            # stock.save()

            # template variable
            completed_files.append(dict(
                date=fdate,
                volume=stock.volume,
                close=stock.close
            ))
    else:
        Stock.objects.bulk_create(stocks)

    # check missing dates
    missing_dates = list()
    bdays = bdate_range(start=start, end=end, freq='B')

    for bday in bdays:
        try:
            Stock.objects.get(
                Q(symbol=symbol) & Q(source='thinkback') &
                Q(date=bday.strftime('%Y-%m-%d'))
            )
        except ObjectDoesNotExist:
            bday = bday.to_datetime()

            if not holiday(bday) and not offday(bday):
                missing_dates.append(bday.strftime('%m/%d/%y'))

    # update underlying
    underlying.thinkback = len(
        Stock.objects.filter(Q(symbol=symbol.upper()) & Q(source='thinkback'))
    )
    underlying.missing_dates = '\n'.join(missing_dates)

    if len(completed_files):
        underlying.updated = False
        underlying.validated = False

    underlying.save()

    # stats
    stats = {
        'count': len(completed_files),
        'start': completed_files[0]['date'] if len(completed_files) else '---',
        'stop': completed_files[-1]['date'] if len(completed_files) else '---',
    }

    template = 'data/import_csv_stock/index.html'
    parameters = dict(
        site_title='Csv Stock import',
        title='Thinkback csv stock import: {symbol}'.format(symbol=symbol.upper()),
        symbol=symbol,
        stats=stats,
        completed_files=completed_files,
        missing_dates=missing_dates
    )

    return render(request, template, parameters)


def change_code(contract, data):
    """
    Check duplicated option code then update option contract into new code
    :param contract: OptionContract
    :param data: dict
    """
    old_contracts = OptionContract.objects.filter(
        Q(option_code__contains=data['option_code']) & Q(expire=True)
    ).order_by('id')
    for c0 in old_contracts:
        if '_' not in c0.option_code:
            c0.option_code = '%s_%d' % (c0.option_code, c0.id)
            c0.code_change = True
            c0.save()

            print '\t\t| DUPLICATED CODE:', data['option_code'],
            print 'EXIST CODE REPLACE WITH:', c0.option_code

    contract.load_dict(data)
    contract.save()


def get_contracts(symbol, error=False):
    """
    Get option contracts that is not expire error or not error free
    :param symbol: str
    :param error: bool
    :return: Series
    """
    if error:
        query = Q(symbol=symbol) & Q(expire=False)
    else:
        query = Q(symbol=symbol) & Q(expire=False) & Q(forfeit=False)

    return pd.Series({
        c.option_code: c for c in
        list(OptionContract.objects.filter(query).order_by('id').all())
    })


def get_dte_date(ex_month, ex_year):
    """
    Use option contract ex_month and ex_year to get dte date
    :param ex_month: str
    :param ex_year: int
    :return: date
    """
    year = int(datetime.datetime.strptime(str('%02d' % ex_year), '%y').strftime('%Y'))
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

    return datetime.date(year=year, month=month, day=day)


def csv_option_import(request, symbol):
    """
    Import thinkback csv options into db
    :param request: request
    :param symbol: str
    :return: render
    """
    symbol = symbol.upper()
    path = os.path.join(BASE_DIR, 'files', 'thinkback', symbol.lower())

    stocks = Stock.objects.filter(Q(symbol=symbol) & Q(source='thinkback')).order_by('date')

    for i, stock in enumerate(stocks):
        # skip if option already exists
        if Option.objects.filter(Q(contract__symbol=symbol) & Q(date=stock.date)).exists():
            continue
        else:
            print '-' * 100
            print '%05d' % i, 'RUNNING', stock.date
            print '-' * 100

        year = stock.date.strftime('%Y')
        fpath = os.path.join(
            path, year, '%s-StockAndOptionQuoteFor%s.csv' % (stock.date, symbol)
        )
        _, option_data = ThinkBack(fpath).read()

        # contracts in db
        contracts = get_contracts(symbol)
        codes0 = contracts.index
        keys = ('name', 'ex_month', 'ex_year', 'special', 'strike')
        dtypes = (str, str, int, str, float)

        # contract in option data
        exist_contracts = list()
        new_contracts = list()
        for data in option_data:
            contract, option = data

            if contract['option_code'] in codes0:
                exist_contracts.append(data)

                # check contract that need update
                c = contracts[contract['option_code']]
                if c.right != contract['right'] or c.others != contract['others']:
                    print '----|UPDATE:', c, '->',
                    c.load_dict(contract)
                    print c
                    c.save()
            else:
                new_contracts.append(data)

        # spec is here after update
        specs = pd.DataFrame(
            [{key: dtype(getattr(contract, key)) for key, dtype in zip(keys, dtypes)}
             for contract in contracts.values],
            index=contracts.index
        )

        # loop new contracts only
        codes1 = np.array([c['option_code'] for c, o in exist_contracts])
        temp_contracts = list()
        for data in new_contracts:
            contract, option = data

            df_specs = pd.DataFrame()
            if not specs.empty:
                df_specs = specs.loc[
                    (specs['name'] == contract['name'])
                    & (specs['ex_month'] == contract['ex_month'])
                    & (specs['ex_year'] == contract['ex_year'])
                    & (specs['special'] == contract['special'])
                    & (specs['strike'] == contract['strike'])
                    # & (specs2['others'] == contract['others'])
                ]

            # spec found in specs, possible change code
            # if spec in specs.values():
            if len(df_specs.index):
                # old option code found and same contract found
                # indexes = np.array([k for k, s in specs.items() if s == spec])
                indexes = df_specs.index

                if len(indexes) > 1:
                    # mean got both split and standard options
                    # get same right option code
                    for index in indexes:
                        if contract['right'] == contracts[index].right:
                            code = index
                            same = contracts[code]
                            break
                else:
                    code = indexes[0]
                    same = contracts[code]

                # check old option code is not exist
                if code in codes1 or contract['others'] != same.others:
                    # mean old code is still running today, no need change
                    # for today option code, it is new option code
                    #print 'current', contract['option_code'], 'old', option_code, 'old found in today'
                    c = OptionContract()
                    c.symbol = symbol
                    c.source = 'thinkback'
                    c.load_dict(contract)
                    temp_contracts.append(c)
                else:
                    #print same_contract
                    if contract['right'] == same.right:
                        if contract['option_code'] in ('VTZMX', 'DIS110122C55', 'DIS110122P55'):
                            print contract['right'], same.right, contract['others'], same.others
                        # same right, so is code change
                        print '--| CODE: CHANGE', code, '->', contract['option_code']
                    else:
                        # right no same, so is split
                        print '--| CODE: SPLIT', code, '->', contract['option_code'],
                        print ';', same.right, '->', contract['right']

                    # change code now
                    change_code(same, contract)
            else:
                # brand new
                c = OptionContract()
                c.symbol = symbol
                c.source = 'thinkback'
                c.load_dict(contract)
                temp_contracts.append(c)
                # print c, 'others:', c.others, 'special:', c.special
        else:
            # add all new contract into db
            try:
                OptionContract.objects.bulk_create(temp_contracts)
            except IntegrityError:
                for c in temp_contracts:
                    try:
                        c.save()
                    except IntegrityError:
                        try:
                            change_code(c, {
                                'ex_month': c.ex_month,
                                'ex_year': c.ex_year,
                                'right': c.right,
                                'strike': c.strike,
                                'special': c.special,
                                'others': c.others,
                                'option_code': c.option_code,
                                'name': c.name
                            })
                        except IntegrityError:
                            # error option code found, use existing
                            pass

        # get contract in db again
        contracts = get_contracts(symbol, error=True)

        # insert option
        options = list()
        for contract, option in option_data:
            # get contract in list
            o = Option()
            o.contract = contracts[contract['option_code']]
            o.load_dict(option)
            options.append(o)
        else:
            Option.objects.bulk_create(options)

        # set expire for today options
        options = Option.objects.filter(Q(contract__symbol=symbol) & Q(date=stock.date))
        for option in options:
            if option.dte == 0:
                print '---| EX. set expire:', option, option.contract.option_code, option.dte
                option.contract.expire = True
                option.contract.save()

        # errors section
        if len(contracts) != options.count():
            codes2 = [o.contract.option_code for o in options]

            for code in contracts.keys():
                if code not in codes2:
                    c = contracts[code]
                    o = c.option_set.order_by('date').last()

                    if o.bid or o.ask:
                        if not c.forfeit and (o.bid > 1000 or o.ask > 1000):
                            print '----| FORFEIT:', c, code, o.bid, o.ask
                            c.forfeit = True
                            c.save()
                        elif o.dte in (1, 2):
                            # it is near to expiration, set expire, maybe no data
                            c.expire = True
                            c.save()
                        else:
                            if c.missing == 0:
                                print '----| MISSING:', c, code, o.bid, o.ask

                            c.missing += 1
                            c.save()

                    # set all error expire
                    dte_date = get_dte_date(c.ex_month, c.ex_year)
                    if dte_date < stock.date:
                        print '----| MISSING/ERROR EXPIRE:', c, code, stock.date
                        c.expire = True
                        c.save()

        # stat sections
        print '| STAT: <', 'contract:', len(contracts), 'options:', options.count(),
        print 'extra:', len(contracts) - options.count(), '>'
        # print 'total:', OptionContract.objects.count(), Option.objects.count()

    # verify contracts
    contracts = OptionContract.objects.filter(symbol=symbol)
    missing_dates = list()
    print '=' * 100 + '\nMISSING CONTRACT\n' + '=' * 100
    for contract in contracts:
        dates0 = np.array([c.date for c in contract.option_set.order_by('date')])
        dates1 = pd.Series([d.date() for d in pd.bdate_range(dates0[0], dates0[-1])])
        dates1 = dates1[dates1.apply(lambda x: not offday(x) and not holiday(x))]

        # save missing into contract
        dates2 = dates1[dates1.apply(lambda x: x not in dates0)]
        missing = dates2.count()
        if missing:
            print '| MISSING', contract, contract.option_code, missing
            contract.missing = missing
            contract.save()
            missing_dates += list(dates2)
        elif contract.missing != missing:
            if missing:
                print '| MISSING', contract, contract.option_code, missing
            contract.missing = missing
            contract.save()

            missing_dates += list(dates2)
    else:
        print '-' * 100 + '\nMISSING DATES\n' + '-' * 100
        missing_dates = pd.Series([d.strftime('%m/%d/%y') for d in missing_dates]).value_counts()
        print missing_dates
        missing_dates = [{'date': k, 'count': v} for k, v in zip(missing_dates.index, missing_dates)]

    print '=' * 100

    # display error contracts
    forfeit_contracts = list()
    print 'FORFEIT CONTRACTS\n' + '=' * 100
    for key, contract in enumerate(contracts.filter(forfeit=True)):
        if contract.forfeit:
            print 'FORFEIT:', contract, contract.forfeit
            forfeit_contracts.append(contract)
    print '\n' + '=' * 100

    # stats
    contracts = OptionContract.objects.filter(symbol=symbol)
    options = Option.objects.filter(contract__symbol=symbol)

    try:
        others_set = [c['others'] for c in contracts.distinct('others').values('others')]
        special_set = [c['special'] for c in contracts.distinct('special').values('special')]
    except NotImplementedError:
        others_set = [c['others'] for c in contracts.values('others').distinct()]
        special_set = [c['special'] for c in contracts.values('special').distinct()]

    stats = {
        'contracts': {
            'count': contracts.count(),
            'expire': contracts.filter(expire=True).count(),
            'split': contracts.filter(split=True).count(),
            'code_change': contracts.filter(code_change=True).count(),
            'others': contracts.exclude(others='').count(),
            'others_set': ', '.join(others_set),
            'special': contracts.exclude(special='Standard').count(),
            'special_set': ', '.join(special_set),
            'missing': contracts.exclude(missing=0).count(),
        },
        'options': {
            'count': options.count(),
        }
    }

    template = 'data/import_csv_option/index.html'
    parameters = dict(
        site_title='Csv Option import',
        title='Thinkback csv option import: {symbol}'.format(symbol=symbol.upper()),
        symbol=symbol.upper(),
        stats=stats,
        missing_dates=missing_dates,
        forfeit_contracts=forfeit_contracts
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
    elif action == 'validated':
        underlying.validated = True
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
                        if '--' not in self.temp:
                            self.data.append(self.temp)

                        self.temp = list()
                        self.start = False

                if data == 'SmartEstimate':
                    self.after_smart_estimate = True

        p = EarningParser()
        p.feed(l)

        # get old earning
        dates = [d['actual_date'] for d in
                 Earning.objects.filter(symbol=symbol).values('actual_date')]

        # update and add new
        earnings = list()
        for l in p.data:
            e = {k: str(v) for k, v in zip(
                ['report_date', 'actual_date', 'release', 'estimate_eps', 'analysts',
                 'adjusted_eps', 'diff', 'hl', 'gaap', 'actual_eps'], l
            )}

            e['quarter'] = e['report_date'].split(' ')[0]
            e['year'] = e['report_date'].split(' ')[1]
            e['actual_date'] = datetime.datetime.strptime(e['actual_date'], '%m/%d/%y').date()
            e['analysts'] = int(e['analysts'][1:-1].replace(' Analysts', ''))
            e['low'] = float(e['hl'].split(' / ')[0])
            e['high'] = float(e['hl'].split(' / ')[1])
            del e['report_date'], e['hl'], e['diff']

            for key in ('estimate_eps', 'adjusted_eps', 'gaap', 'actual_eps'):
                e[key] = float(e[key])

            if e['actual_date'] not in dates:
                earning = Earning(**e)
                earning.symbol = symbol
                earnings.append(earning)
        else:
            Earning.objects.bulk_create(earnings)

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

        # do not duplicate insert
        dates = [d['expire_date'] for d in Dividend.objects.filter(symbol=symbol).values('expire_date')]

        dividends1 = list()
        for l in p.data:
            d = {k: str(v) for k, v in zip(
                ['year', 'quarter', 'announce_date', 'expire_date',
                 'record_date', 'payable_date', 'amount', 'dividend_type'], l
            )}

            for date in ('announce_date', 'expire_date', 'record_date', 'payable_date'):
                d[date] = datetime.datetime.strptime(d[date], '%d/%M/%Y').date()

            dividend = Dividend(**d)
            dividend.symbol = symbol
            dividend.status = True

            if d['expire_date'] not in dates:
                dividends1.append(dividend)
        else:
            Dividend.objects.bulk_create(dividends1)


def event_import(request, event, symbol):
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
                    return redirect(reverse('admin:data_earning_changelist') + '?q=' + symbol)
                else:
                    form.insert_dividend()
                    return redirect(reverse('admin:data_dividend_changelist') + '?q=' + symbol)
        else:
            form = EventImportForm(
                initial={
                    'symbol': symbol.upper(),
                    'event': event
                }
            )

    else:
        raise Http404("Verify event name not found.")

    template = 'data/event_import/index.html'
    parameters = dict(
        site_title='Verify {event}'.format(event=event),
        title='Verify {event}'.format(event=event),
        form=form
    )

    return render(request, template, parameters)