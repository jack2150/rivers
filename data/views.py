import codecs
from datetime import datetime
from glob import glob
import os
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import render
import numpy as np
from pandas import bdate_range
from pandas.io.data import get_data_google, get_data_yahoo
from data.extra import *
from data.io.thinkback import ThinkBack
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
        underlying.google += len(stocks)
    else:
        underlying.yahoo += len(stocks)

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


def csv_quote_import(request, symbol):
    """
    CSV import thinkback files into db
    :param request: request
    :param symbol: str
    :return: render
    """
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
    for f in files:
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
            print 'running %s file...' % os.path.basename(f)

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

            # insert option contract and option using bulk create
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
                option.option_contract = option_contract
                option.load_dict(option_dict)

                options.append(option)

            # insert options
            Option.objects.bulk_create(options)
            saved[-1]['options'] = len(options)

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
                option.option_contract = contract
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




















