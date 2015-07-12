import codecs
from datetime import datetime
from glob import glob
import os
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import render
import numpy as np
from pandas import bdate_range
from pandas.io.data import get_data_google, get_data_yahoo
from data.extra import *
from data.plugin.thinkback import ThinkBack
from data.models import *
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
    end = pd.datetime.today().date()

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
    data = f(symbols=symbol, start=start, end=end, adjust_price=True)

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
        underlying.yahoo = Stock.objects.filter(Q(symbol=symbol) & Q(source='google')).count()

    underlying.stop = end
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


def rename_option_code(c, option_code):
    old_contracts = OptionContract.objects.filter(
        Q(option_code__contains=option_code) & Q(expire=True)
    ).order_by('id')
    for c0 in old_contracts:
        if '_' not in c0.option_code:
            c0.option_code = '%s_%d' % (c0.option_code, c0.id)
            c0.save()
            print '\t\tD. duplicated', option_code, 'new code:', c0.option_code
    c.option_code = option_code
    c.save()


def csv_quote_import(request, symbol):
    """
    CSV import thinkback files into db
    :param request: request
    :param symbol: str
    :return: render
    """
    # core lambda
    get_contracts = lambda x: list(OptionContract.objects.filter(
        Q(symbol=x) & Q(expire=False)
    ).order_by('id').all())

    # get underlying
    underlying = Underlying.objects.get(symbol=symbol.upper())
    start = underlying.start
    end = pd.datetime.today()

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
                os.rename(no_year_file, os.path.join(year_dir, filename))

    # get all files in year folder
    files = []
    for year in glob(os.path.join(path, '*')):
        for csv in glob(os.path.join(year, '*.csv')):
            files.append(csv)

    # start save csv
    saved = list()

    for i, f in enumerate(files):
        # get date and symbol
        date, symbol = os.path.basename(f)[:-4].split('-StockAndOptionQuoteFor')

        # check exists
        exists = Stock.objects.filter(
            Q(symbol=symbol) & Q(date=date) & Q(source='thinkback')
        ).exists()

        bday = datetime.strptime(date, '%Y-%m-%d')
        trading_day = not (holiday(bday) or offday(bday))

        if not exists and trading_day:
            # output to console
            print '%d. running %s file...' % (i, os.path.basename(f))

            stock_data, option_data = ThinkBack(f).read()

            if not long(stock_data['volume']):
                continue  # skip this part

            # save stock
            stock = Stock()
            stock.symbol = symbol
            stock.load_dict(stock_data)
            stock.source = 'thinkback'
            stock.save()

            # template variable
            saved.append(dict(
                fname=os.path.basename(f),
                stock=stock,
                contracts=0,
                options=0
            ))

            contracts0 = get_contracts(symbol)
            contracts1 = list()
            codes = [c.option_code for c in contracts0]
            keys1 = ('name', 'ex_month', 'ex_year', 'others', 'special', 'strike')
            keys2 = ('name', 'ex_month', 'ex_year', 'right', 'others', 'special', 'strike')
            half_specs = [tuple([getattr(c, k) for k in keys1]) for c in contracts0]
            full_specs = [tuple([getattr(c, k) for k in keys2]) for c in contracts0]

            #if len(specs):
            #    print specs[0]
            """
              1. if contract in codes, use original
              2. if contract not in codes
              2a. check same specs
              """
            exists = list()
            unknowns = list()
            for data in option_data:
                contract, option = data

                if contract['option_code'] in codes:
                    exists.append(data)
                else:
                    unknowns.append(data)

            # all not in codes
            codes2 = [c['option_code'] for c, _ in exists]
            for data in unknowns:
                contract, option = data
                spec = tuple([contract[k] for k in keys1])
                fspec = tuple([contract[k] for k in keys2])

                """
                this 2 should be change code
                AIGMD -> IKGMD
                AIGAD -> IKGAD
                """
                if contract['option_code'] == 'IKGMD':


                    print 'AIGMD', 'AIGMD' in codes, 'AIGMD' in codes2,
                    print 'IKGMD', 'IKGMD' in codes, 'IKGMD' in codes2,
                    print 'spec', spec, spec in half_specs, spec in full_specs

                    print OptionContract.objects.get(option_code='AIGMD')


                if fspec in full_specs:
                    # same right but different code, do rename
                    c = OptionContract.objects.get(
                        option_code=codes[half_specs.index(spec)],
                        ex_month=contract['ex_month'],
                        ex_year=contract['ex_year'],
                        name=contract['name'],
                        right=contract['right'],
                        others=contract['others'],
                        special=contract['special'],
                        strike=contract['strike'],
                    )

                    rename_option_code(c, contract['option_code'])
                elif spec in half_specs:


                    # different right and different code
                    c = OptionContract.objects.get(
                        option_code=codes[half_specs.index(spec)],
                        ex_month=contract['ex_month'],
                        ex_year=contract['ex_year'],
                        name=contract['name'],
                        others=contract['others'],
                        special=contract['special'],
                        strike=contract['strike'],
                    )

                    if contract['option_code'] == 'IKGMD':
                        print c.option_code in codes2, 'in today option'
                        print c.right, contract['right']

                    if c.option_code in codes2:
                        # old code is exists in today option, add this as new
                        c = OptionContract()
                        c.symbol = symbol
                        c.source = 'thinkback'
                        c.load_dict(contract)
                        contracts1.append(c)
                    else:
                        # old code not in today option, update old into new
                        # todo: split to split code change, and normal to normal code change

                        print '\tCODE:', c,
                        print 'update', c.option_code, '->', contract['option_code'], 'and',
                        print c.right, '->', contract['right'],
                        if c.right != contract['right']:
                            print 'Reason: SPLIT'
                        else:
                            print 'Reason: CODE CHANGE'

                        try:
                            c.option_code = contract['option_code']
                            c.save()
                        except IntegrityError:
                            # got duplicated old option code
                            rename_option_code(c, contract['option_code'])
                else:
                    # brand new
                    c = OptionContract()
                    c.symbol = symbol
                    c.source = 'thinkback'
                    c.load_dict(contract)
                    contracts1.append(c)
            else:
                # finish add into contracts
                # todo: duplicated option code
                try:
                    OptionContract.objects.bulk_create(contracts1)
                except IntegrityError:
                    for c in contracts1:
                        try:
                            c.save()
                        except IntegrityError:
                            rename_option_code(c, c.option_code)

                contracts0 = get_contracts(symbol)  # update
                contracts = {c.option_code: c for c in contracts0}

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

            # set expire
            options = Option.objects.filter(Q(contract__symbol=symbol) & Q(date=date))
            for option in options:
                if option.dte == 0:
                    print '\tEX. set expire:', option, option.dte
                    option.contract.expire = True
                    option.contract.save()

            contract_count = OptionContract.objects.count()
            option_count = Option.objects.count()
            print '.. S. today stat: <', 'contract:', len(contracts), 'options:', options.count(), '>',
            print 'total:', OptionContract.objects.count(), Option.objects.count()

            if len(contracts) > options.count():
                codes3 = [c.contract.option_code for c in options]

                for option_code in contracts.keys():
                    if option_code not in codes3:
                        print option_code
                break

            # todo: some expire contract not set expire...


            """
            for data in option_data:
                contract, option = data
                #print sorted(contract.keys())



                #print contract
                if contract['option_code'] == 'UZLGA':
                    print 'UZLGA', 'UZLGA' in codes

                if contract['option_code'] not in codes:
                    #print 'new contract'
                    spec = tuple([contract[k] for k in keys])

                    if spec in specs:
                        c = OptionContract.objects.get(
                            option_code=codes[specs.index(spec)],
                            ex_month=contract['ex_month'],
                            ex_year=contract['ex_year'],
                            name=contract['name'],
                            others=contract['others'],
                            special=contract['special'],
                            strike=contract['strike'],
                        )


                        print c, c.option_code, '->', contract['option_code']

                        c.option_code = contract['option_code']
                        c.save()



                        # same contract specs, but different right and option code
                        #print codes[specs.index(spec)],
                        #print 'found same', contract['others'],
                        #print '-> new code ->', contract['option_code']
                        # todo: do upgrade, if existing code no new option, others is different
                        # todo: need 'AIGAN' -> 'AZJAN' on 07-01-2009


                    else:
                        # insert new
                        c = OptionContract()
                        c.symbol = symbol
                        c.source = 'thinkback'
                        c.load_dict(contract)
                        contracts1.append(c)
                    # check is split


                    #print contract['option_code'], 'found'
                #else:
                    #print contract['option_code'], 'NOT FOUND ...'

            else:
                # finish add into contracts
                OptionContract.objects.bulk_create(contracts1)

                # update again
                contracts0 = list(OptionContract.objects.filter(symbol=symbol).all())
                print len(contracts0)

            """

            # insert option contract and option using bulk create
            # todo: roll back, need option code update
            """
            option_codes = [contract['option_code'] for contract, _ in option_data]

            size = 100
            exists_option_codes = list()
            for chunk in [option_codes[i:i + size] for i in range(0, len(option_codes), size)]:
                exists_option_codes += [x[0] for x in OptionContract.objects.filter(
                    option_code__in=chunk).values_list('option_code')]

            new_option_codes = set(option_codes) - set(exists_option_codes)

            contracts = list()
            for option_code in set(option_codes):
                if option_code in new_option_codes:
                    try:
                        contract_dict = [
                            c for c, _ in option_data if c['option_code'] == option_code
                        ][0]
                    except IndexError:
                        raise Exception()

                    contract = OptionContract()
                    contract.symbol = symbol
                    contract.source = 'thinkback'
                    contract.load_dict(contract_dict)
                    contracts.append(contract)

            # insert option contract
            OptionContract.objects.bulk_create(contracts)
            saved[-1]['contracts'] = len(contracts)

            # option section now
            option_contracts = list()
            for chunk in [option_codes[i:i + size] for i in range(0, len(option_codes), size)]:
                option_contracts += [
                    option_contract for option_contract in
                    OptionContract.objects.filter(option_code__in=chunk)
                ]

            options = list()
            for contract_dict, option_dict in option_data:
                try:
                    option_contract = [
                        option_contract for option_contract in option_contracts
                        if option_contract.option_code == contract_dict['option_code']
                    ][0]
                except IndexError:
                    raise IndexError('Contract not inserted...')

                option = Option()
                option.contract = option_contract
                option.load_dict(option_dict)

                options.append(option)

            # insert options
            Option.objects.bulk_create(options)
            saved[-1]['options'] = len(options)
            """

    # update stat
    underlying.thinkback = len(
        Stock.objects.filter(Q(symbol=symbol.upper()) & Q(source='thinkback'))
    )
    underlying.stop = end
    underlying.save()

    # missing files between dates
    missing = list()
    if underlying.thinkback > 2:
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
                    missing.append(bday.strftime('%m/%d/%y'))

    template = 'data/import_csv.html'
    parameters = dict(
        site_title='Csv import',
        title='Thinkback Csv import: {symbol}'.format(symbol=symbol.upper()),
        symbol=symbol,
        files=saved[:5] + [None] + saved[-5:] if len(saved) > 10 else saved,
        missing=','.join(missing)
    )

    return render(request, template, parameters)


# noinspection PyUnresolvedReferences
def daily_quote_import(request):
    """
    Import csv in daily folder and put all csv into correct folder
    :param request: request
    :return: render
    """
    path = os.path.join(BASE_DIR, 'files', 'thinkback', '__daily__')
    files = glob(os.path.join(path, '*.csv'))

    saved = list()
    for f in files:
        fname = os.path.basename(f)
        date, symbol = fname.split('-StockAndOptionQuoteFor')
        symbol = symbol.upper()[:-4]

        # file into dict
        stock_data, option_data = ThinkBack(f).read()

        try:
            Stock.objects.get(symbol=symbol, source='thinkback', date=date)
        except ObjectDoesNotExist:
            print 'running %s file...' % os.path.basename(f)

            # get underlying
            underlying = Underlying.objects.get(symbol=symbol)

            # save stock
            stock = Stock()
            stock.symbol = symbol
            stock.source = 'thinkback'
            stock.load_dict(stock_data)
            stock.save()

            # template variable
            saved.append(dict(
                fname=os.path.basename(f),
                stock=stock,
                contracts=0,
                options=0
            ))

            # save contract and option
            contracts = 0
            options = 0
            for contract_dict, option_dict in option_data:
                try:
                    contract = OptionContract.objects.get(option_code=contract_dict['option_code'])
                except ObjectDoesNotExist:
                    contract = OptionContract()
                    contract.symbol = symbol
                    contract.source = 'tos_thinkback'
                    contract.load_dict(contract_dict)
                    contract.save()
                    contracts += 1
                    saved[-1]['contracts'] += 1

                option = Option()
                option.contract = contract
                option.load_dict(option_dict)
                option.save()
                options += 1
                saved[-1]['options'] += 1

            # move file into folder
            year = fname[:4]
            year_dir = os.path.join(BASE_DIR, 'files', 'thinkback', symbol, year)

            # make dir if not exists
            if not os.path.isdir(year_dir):
                os.mkdir(year_dir)

            # move file into folder
            os.rename(f, os.path.join(year_dir, os.path.basename(f)))

            # save data from web
            google_data = {
                key.lower(): value for key, value in
                dict(get_data_google(
                    symbols=symbol, start=date, end=date, adjust_price=True
                ).ix[date]).items()
            }
            yahoo_data = {
                key.lower(): value for key, value in
                dict(get_data_yahoo(
                    symbols=symbol, start=date, end=date, adjust_price=True
                ).ix[date]).items()
            }

            google_data['date'] = date
            print google_data
            stock = Stock()
            stock.symbol = symbol
            stock.source = 'google'
            stock.load_dict(google_data)
            stock.save()

            yahoo_data['date'] = date
            stock = Stock()
            stock.symbol = symbol
            stock.source = 'yahoo'
            stock.load_dict(yahoo_data)
            stock.save()

            # update underlying
            underlying.thinkback += 1
            underlying.google += 1
            underlying.yahoo += 1
            underlying.stop = date
            underlying.save()

    template = 'data/import_daily.html'
    parameters = dict(
        site_title='Daily import',
        title='Daily import',
        files=saved
    )

    return render(request, template, parameters)


# noinspection PyUnresolvedReferences
def csv_calendar_import(request, event):
    """
    Import dividend using csv files in calendar folder
    :param request: request
    :return: render
    """
    if event == 'dividend':
        folder_name = 'dividends'
        obj_class = Dividend
    elif event == 'earning':
        folder_name = 'earnings'
        obj_class = Earning
    else:
        raise ValueError('Calender event can only be "dividend" or "earning".')

    path = os.path.join(BASE_DIR, 'files', 'calendars', folder_name)

    files = sorted(glob(os.path.join(path, '*.csv')))

    saved = list()
    events = list()
    for f in files:
        lines = codecs.open(f, encoding="ascii", errors="ignore").readlines()

        # skip duplicate files
        date = datetime.strptime(lines[2].rstrip(), '%m/%d/%y').date()

        # make condition
        if event == 'dividend':
            c = Q(expire_date=date)
        else:
            #c = Q(date_est=date) & (Q(date_act__lte=date) | Q(date_act__isnull=True))
            c = Q(date_est__gte=date) & (Q(date_act=date) | Q(date_act__isnull=True))

        if obj_class.objects.filter(c).exists():
            #print 'skip: ', f
            continue
        else:
            print 'running:', f

        for line in lines[4:]:
            event_obj = obj_class()
            event_obj.load_csv(line)
            events.append(event_obj)

        if len(events) > 500:
            # every time insert 500 dividends
            obj_class.objects.bulk_create(events)
            events = list()

        saved.append(dict(
            fname=f,
            date=date,
            event=len(lines)
        ))
    else:
        if len(events):
            obj_class.objects.bulk_create(events)

    #Dividend.objects.all().delete()
    template = 'data/import_calendar.html'
    parameters = dict(
        site_title='{event} import'.format(event=event.capitalize()),
        title='{event} import'.format(event=event.capitalize()),
        event=event,
        files=saved[:5] + [None] + saved[-5:] if len(saved) > 10 else saved,
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


def verify_options(request, symbol):
    """
    1. get option contract
    2. contract loop - start date - last date
    :param request: request
    :param symbol: str
    :return: render
    """
    print symbol
    stocks = Stock.objects.filter(Q(symbol=symbol) & Q(source='thinkback')).order_by('date')
    stocks2 = Stock.objects.filter(Q(symbol=symbol) & Q(source='google')).order_by('date')
    #print stocks[0], stocks2[0]
    #print stocks.get(date='2009-06-30'), stocks2.get(date='2009-06-30')
    #print stocks.get(date='2009-07-01'), stocks2.get(date='2009-07-01')
    #print stocks.get(date='2015-03-30'), stocks2.get(date='2015-03-30')

    #for d in [s['date'] for s in stocks.values('date')]:
    #    s = stocks.get(date=d)
    #    s2 = stocks2.get(date=d)
    #    print s.date, s2.date, s.close, s2.close, s.close == s2.close

    """
    stock_dates = [s['date'] for s in stocks.values('date')]
    date0 = stocks[0].date
    date1 = stocks[stocks.count() - 1].date
     """

    # do not verify special
    contracts = OptionContract.objects.filter(
        Q(symbol=symbol) & Q(special__in=('Standard', 'Weekly', 'Mini'))
    )

    missing = list()
    for contract in contracts[:1]:
        print contract.option_code
        print contract.option_set.count()
        
        o1 = OptionContract.objects.filter(
            symbol=symbol,
            ex_month=contract.ex_month,
            ex_year=contract.ex_year,
            right=contract.right,
            special=contract.special,
            strike=contract.strike,
            name=contract.name,
            #option_code=values['option_code'],
            others=contract.others,
        )
        for o in o1:
            print o, o.option_code
            d = list(o.option_set.order_by('date').values('date'))
            print d[0], d[-1], len(d)
        # todo: split problem on option code change and

        """

        options = contract.option_set.order_by('date')
        start = options[0].date
        end = options[options.count() - 1].date
        print options[0], options[options.count() - 1]

        dates = [d.date() for d in pd.date_range(start, end, freq='B')]

        for date in dates:
            try:
                option = options.get(date=date)
                #print 'found', option
            except ObjectDoesNotExist:
                if holiday(date) or offday(date):
                    print 'is holiday or off days'
                elif date not in stock_dates:
                    print date, 'stock date not exists too...'
                else:
                    print contract, date, 'not found...'

        # get first date of contract
        # todo: option code change?



    """
    template = 'data/verify_options.html'
    parameters = dict(
        site_title='Verify options',
        title='Verify options'
    )

    return render(request, template, parameters)

"""
6-15 ,,0,.005,.00,.00,.00,.00,,++,0.00%,100.00%,2.19%,0,"19,348",0,.005,WAPAN,0,.01,JAN 10,70,68.30,68.50,0,68.400,.00,.00,.00,.00,,++,100.00%,0.00%,2.19%,0,6,68.47,-.07,WAPMN,,
6-16 ,,0,.005,.00,.00,.00,.00,,++,0.00%,100.00%,2.11%,0,"19,348",0,.005,AIGAN,0,.01,JAN 10,70,68.35,68.65,0,68.500,.00,.00,.00,.00,,++,100.00%,0.00%,2.11%,0,6,68.52,-.02,AIGMN,,
check is download error or option code really change?
"""











