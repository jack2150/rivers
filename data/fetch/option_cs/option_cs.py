from django.core.exceptions import ObjectDoesNotExist
from data.models import *
from django.db.models import Q
import numpy as np
from pandas.tseries.offsets import BDay


def get_options_by_cycle_strike(symbol, name, dates0, dte, moneyness, cycle, strike):
    """
    Get a list of options using cycle and strike
    :param symbol: str
    :param name: str
    :param dates0: list of date
    :param dte: int
    :param moneyness: str ('ITM', 'OTM')
    :param cycle: int
    :param strike: int
    :return: list of date, list of Option
    """
    query = (Q(contract__symbol=symbol) &
             Q(contract__name=name)
             & Q(contract__others='')
             & Q(contract__forfeit=False)
             & Q(contract__missing__lt=5)
             & Q(contract__right='100'))

    dates1 = [d for d in dates0]

    if name == 'CALL' and moneyness == 'OTM':
        m_query = Q(intrinsic=0)
        order = 1
    elif name == 'CALL' and moneyness == 'ITM':
        m_query = Q(intrinsic__gt=0)
        order = -1
    elif name == 'PUT' and moneyness == 'OTM':
        m_query = Q(intrinsic=0)
        order = -1
    elif name == 'PUT' and moneyness == 'ITM':
        m_query = Q(intrinsic__gt=0)
        order = 1
    else:
        raise ValueError('Do not support ATM, use ITM strike 1 instead.')

    df_options = pd.DataFrame(list(Option.objects.filter(
        query
        & Q(date__in=set(dates0))
        & Q(dte__gte=dte)
        & m_query
    ).values('id', 'date', 'dte', 'bid', 'ask', 'contract__strike')))

    # find missing dates
    missing_dates = [d1 for d1 in dates0 if d1 not in list(df_options['date'])]

    options = list()
    for d1 in missing_dates:
        drange = [(d1 + BDay(i)).to_datetime().date() for i in (-1, 1, -2, 2, -3, 3)]
        df_drange = pd.DataFrame(list(Option.objects.filter(
            query
            & Q(date__in=drange)
            & Q(dte__gte=dte)
            & m_query
        ).values('id', 'date', 'dte', 'bid', 'ask', 'contract__strike')))

        for d2 in drange:
            try:
                df_found = df_drange[df_drange['date'] == d2]
                if len(df_found):
                    options.append(df_found)
                    dates1[dates1.index(d1)] = d2
                    break
            except KeyError:
                pass
        else:
            # not found too
            dates1[dates1.index(d1)] = None
    else:
        # append back into options
        if len(options):
            df_options = pd.concat([df_options] + options)

    option_dates = df_options['date'].unique()

    ids = list()
    for date in option_dates:
        df = df_options[df_options['date'] == date]

        try:
            cycles = np.sort(df['dte'].unique())
            strikes = np.sort(df[df['dte'] == cycles[cycle]]['contract__strike'].unique())[::order]

            df_found = df.loc[
                (df['dte'] == cycles[cycle])
                & (df['contract__strike'] == strikes[strike])
            ]

            # only have
            if df_found['bid'].values[0] or df_found['ask'].values[0]:
                ids.append(
                    df_found['id'].values[0]
                )
            else:
                dates1[dates1.index(date)] = None
        except IndexError:
            # when cycle or strike not found, skip
            print symbol, date, cycle, strike, 'cycle or strike not found.'
            dates1[dates1.index(date)] = None

    options = Option.objects.filter(id__in=ids)

    return dates1, options


def get_option_by_contract_date(contract, date0):
    """
    Get option by contract and date
    :param contract: OptionContract
    :param date0: date
    :return: date, Option
    """
    option = None
    date1 = date0
    try:
        option = Option.objects.get(Q(contract=contract) & Q(date=date0))
    except ObjectDoesNotExist:
        drange = [(date0 + BDay(i)).to_datetime().date() for i in (-1, 1, -2, 2, -3, 3)]
        exist_dates = np.array([o['date'] for o in Option.objects.filter(
            Q(contract=contract) & Q(date__in=drange)
        ).only('date').values('date')])

        for d in drange:
            if d in exist_dates:
                date1 = d
                option = Option.objects.get(Q(contract=contract) & Q(date=d))
                break

    return date1, option

    # todo: move this as u func