import calendar
import datetime
from glob import glob
import os
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import render
from pandas import bdate_range
from data.extra import holiday, offday
from data.models import *
from data.plugin.thinkback import ThinkBack
from rivers.settings import BASE_DIR
import numpy as np


def change_code(contract0, contract1):
    """
    Check duplicated option code then update option contract into new code
    :param contract0: OptionContract
    :param contract1: dict
    """
    old_contracts = OptionContract.objects.filter(
        Q(option_code__contains=contract1['option_code']) & Q(expire=True)
    ).order_by('id')
    for c0 in old_contracts:
        if '_' not in c0.option_code:
            c0.option_code = '%s_%d' % (c0.option_code, c0.id)
            c0.save()
            print '\t\tD. duplicated: current code', contract1['option_code'], 'old code:', c0.option_code

    contract0.load_dict(contract1)
    contract0.change_code = True
    contract0.save()


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


def get_dte(ex_month, ex_year):
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


def csv_quote_import2(request, symbol):
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
    no_data_dates = list()
    for i, f in enumerate(files):
        # get date and symbol
        fdate, symbol = os.path.basename(f)[:-4].split('-StockAndOptionQuoteFor')

        # check exists
        exist_contract = Stock.objects.filter(
            Q(symbol=symbol) & Q(date=fdate) & Q(source='thinkback')
        ).exists()

        bday = datetime.datetime.strptime(fdate, '%Y-%m-%d')
        trading_day = not (holiday(bday) or offday(bday))

        if not exist_contract and trading_day:
            # output to console
            print '-' * 100
            print '%05d' % i, 'RUNNING', os.path.basename(f)
            print '-' * 100

            stock_data, option_data = ThinkBack(f).read()

            if long(stock_data['volume']) == 0:
                no_data_dates.append(datetime.datetime.strptime(fdate, '%Y-%m-%d').date())
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

            # contracts in db
            contracts = get_contracts(symbol)
            codes0 = contracts.index
            keys = ('name', 'ex_month', 'ex_year', 'special', 'strike')
            dtypes = (str, str, int, str, float)
            specs = pd.DataFrame(
                [{key: dtype(getattr(contract, key)) for key, dtype in zip(keys, dtypes)}
                 for contract in contracts.values],
                index=contracts.index
            )

            # contract in option data
            exist_contracts = list()
            new_contracts = list()
            for data in option_data:
                contract, option = data

                if contract['option_code'] in codes0:
                    exist_contracts.append(data)
                else:
                    new_contracts.append(data)

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
                        #& (specs2['others'] == contract['others'])
                        & (specs['special'] == contract['special'])
                        & (specs['strike'] == contract['strike'])
                    ]

                # spec found in specs, possible change code
                #if spec in specs.values():
                if len(df_specs.index):
                    # old option code found and same contract found
                    #indexes = np.array([k for k, s in specs.items() if s == spec])
                    indexes = df_specs.index

                    if len(indexes) > 1:
                        # mean got both split and standard options
                        # get same right option code
                        for index in indexes:
                            if contract['right'] == contracts[index].right:
                                code = index
                                same = contracts[code]
                    else:
                        code = indexes[0]
                        same = contracts[code]

                    # check old option code is not exist
                    if code in codes1:
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
                        if contract['others'] == same.others:
                            if contract['right'] == same.right:
                                # same right, so is code change
                                print '--| CODE: CHANGE', code, '->', contract['option_code']
                            else:
                                # right no same, so is split
                                print '--| CODE: SPLIT', code, '->', contract['option_code'],
                                print ';', same.right, '->', contract['right']
                        else:
                            print '--| CODE: OTHERS', code, '->', contract['option_code'],
                            print ';', same.others, '->', contract['others']

                        # change code now
                        change_code(same, contract)
                else:
                    # brand new
                    c = OptionContract()
                    c.symbol = symbol
                    c.source = 'thinkback'
                    c.load_dict(contract)
                    temp_contracts.append(c)
                    #print c, 'others:', c.others, 'special:', c.special
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
            options = Option.objects.filter(Q(contract__symbol=symbol) & Q(date=fdate))
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

                        #if c.errors == '' and (o.bid == 0 and o.ask == 0):
                        #    print '----| DROP:', c, code, o.bid, o.ask
                        #    c.add_errors('DROP')
                        #    c.save()
                        #elif o.bid or o.ask:
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
                        dte = get_dte(c.ex_month, c.ex_year)
                        if dte < datetime.datetime.strptime(fdate, '%Y-%m-%d').date():
                            print '----| MISSING/ERROR EXPIRE:', c, code, fdate
                            c.expire = True
                            c.save()

            # stat sections
            print '| STAT: <', 'contract:', len(contracts), 'options:', options.count(),
            print 'extra:', len(contracts) - options.count(), '>'
            #print 'total:', OptionContract.objects.count(), Option.objects.count()

    # verify contracts
    contracts = OptionContract.objects.filter(symbol=symbol)
    missing_dates = list()
    print '=' * 100 + '\nMISSING CONTRACT\n' + '=' * 100
    for contract in contracts:
        dates0 = np.array([c.date for c in contract.option_set.order_by('date')])
        dates1 = pd.Series([d.date() for d in pd.bdate_range(dates0[0], dates0[-1])])
        dates1 = dates1[dates1.apply(
            lambda x: not offday(x) and not holiday(x) and x not in no_data_dates
        )]

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
        print pd.Series([d.strftime('%m/%d/%y') for d in missing_dates]).value_counts()
        #for date in p.set(missing_dates)):
        #    print 'MISSING DATE:', date

    print '=' * 100

    # display error contracts
    print 'FORFEIT CONTRACTS\n' + '=' * 100
    for key, contract in enumerate(contracts.filter(forfeit=True)):
        if contract.forfeit:
            print 'FORFEIT:', contract, contract.forfeit,
    print '=' * 100

    underlying.thinkback = len(
        Stock.objects.filter(Q(symbol=symbol.upper()) & Q(source='thinkback'))
    )
    underlying.stop = end
    underlying.save()

    # missing files between dates
    dates2 = list()
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
                    dates2.append(bday.strftime('%m/%d/%y'))

    template = 'data/import_csv.html'
    parameters = dict(
        site_title='Csv import',
        title='Thinkback Csv import: {symbol}'.format(symbol=symbol.upper()),
        symbol=symbol,
        files=saved[:5] + [None] + saved[-5:] if len(saved) > 10 else saved,
        missing=','.join(dates2)
    )

    return render(request, template, parameters)

# todo: speed up using np.array and pd.Series

















