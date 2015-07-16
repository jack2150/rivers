from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
import pandas as pd
import numpy as np
from pandas.tseries.offsets import Day, BDay
from data.models import *


def get_options2(options, date, dte, moneyness, cycle, strike):
    """

    :param options:
    :param date:
    :param dte:
    :param moneyness:
    :param cycle:
    :param strike:
    :return:
    """
    option = None
    for d in (date, date - BDay(1), date + BDay(1)):
        # get cycles options
        options1 = options.filter(Q(date=d) & Q(dte__gte=dte))
        cycles = [o['dte'] for o in options1.distinct('dte').values('dte')]

        try:
            options1 = options1.filter(date=d).filter(dte=cycles[cycle])

            if moneyness == 'OTM':
                options2 = options1.filter(Q(intrinsic=0))
                try:
                    option = options2[strike]
                except IndexError:
                    # if strike not exist, then skip
                    pass
            elif moneyness == 'ITM':
                options2 = options1.filter(Q(intrinsic__gt=0))
            else:
                # ATM
                pass
        except IndexError:
            # skip trade because no enough cycle data
            option = None

        if option:
            break

    return option


def get_option1(contract, date):
    """

    :param contract:
    :param date:
    :return:
    """
    option = None
    for d in (date, date - BDay(1), date + BDay(1)):
        try:
            option = Option.objects.get(
                contract=contract,
                date=d
            )

            break
        except ObjectDoesNotExist:
            pass

    return option


def create_order(df_stock, df_signal, moneyness=('ATM', 'ITM', 'OTM'), cycle=10, strike=0):
    """
    Long call option
    1. need data, but cannot get all data
    what option to get? which spread, expiration, cycle??

    date0 -> get date options -> use dte to choose cycle -> get option

    u got date0 and date1
    a. what cycle of dte?
    b. otm, itm, or atm?
    c. what strike in call?
    d.

    """
    # todo: some have 52 days, check why, maybe third week is wrong
    symbol = df_stock.ix[df_stock.index.values[0]]['symbol']

    df_signal2 = df_signal.copy()

    df_signal2['holding'] = df_signal2['holding'].apply(
        lambda x: x / np.timedelta64(1, 'D')
    ).astype(np.int)

    #print df_signal2['holding'].unique()

    options = Option.objects.filter(
        Q(contract__symbol=symbol)
        & Q(contract__name='CALL')
        & Q(contract__others='')
        & Q(contract__others='')
        & Q(contract__forfeit=False)
        & Q(contract__missing__lt=5)
    )

    data = list()
    for index, signal in df_signal2.iterrows():
        holding = int(signal['holding'])

        option0 = get_options2(options, signal['date0'], holding, moneyness, cycle, strike)

        if option0:
            option1 = get_option1(option0.contract, signal['date1'])
        else:
            option1 = None

        print signal['date0'], option0
        print signal['date1'], option1
        print ''




        """
        if option0:
            try:
                option1 = options.get(
                    Q(date=data['date1'])
                    & Q(contract=option0.contract)
                )

                #print option0, '->', option1
            except ObjectDoesNotExist:
                option1 = options.filter(
                    #Q(date__range=(data['date1'] - BDay(3), data['date1'] + BDay(1)))
                    Q(contract=option0.contract)
                ).order_by('date').last()

                #print data['close0'], data['date0'], data['date1'], data['holding']
                if (data['date1'] - BDay(3)).date() > option1.date:

                    print option1.date - option0.date, option0, '-> skip trade', option1, '<<<'
                    # todo: problem
                else:
                    print option1.date - option0.date, option0, '-> not found', option1
        else:
            print 'skip trade, option0 not found'
        """





                #print cycles


        """
        holding = int(data['holding'])
        if holding != 45:
            print data['close0'], data['date0'], data['date1'], data['holding']
            options = Option.objects.filter(
                Q(contract__symbol=symbol)
                & Q(contract__name='CALL')  # todo: need to change name
            )

            options = options.filter(
                Q(date=data['date0'])
                & Q(dte__range=(holding - 3, holding + 3))
            )

            print options.count()
            #print options.distinct('dte').values('dte')
            for option in options:
                print option, option.dte
        """




    return df_signal


# todo: need to verify option
# todo: fslr and bac missing dates