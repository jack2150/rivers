import logging
import numpy as np


logger = logging.getLogger('views')


def get_cycle_strike(df_all, date0, date1, name, close, cycle, strike):
    """

    :param df_all:
    :param date0:
    :param date1:
    :param name: str ('CALL', 'PUT')
    :param close: float
    :param cycle: int
    :param strike: int
    :return:
    """
    df_date = df_all.query('date == %r & name == %r & dte >= %r' % (
        date0, name, (date1 - date0).days
    ))
    # print df_date.to_string(line_width=1000)

    cycles = np.sort(df_date['dte'].unique())
    if cycle < 0:
        raise ValueError('Cycle value cannot be negative')
    elif cycle > len(cycles):
        raise ValueError('Cycle is greater than cycle length')
    else:
        df_cycle = df_date.query('dte == %r' % cycles[cycle]).sort_values('strike')
        # print df_cycle.to_string(line_width=1000)

    strikes = np.sort(df_cycle['strike'])
    atm = np.argmin(np.abs(strikes - close))
    # 0 id is always refer to first OTM strike
    if name == 'CALL':
        if close > strikes[atm]:
            atm += 1
        atm += strike
    elif name == 'PUT':
        if close < strikes[atm]:
            atm -= 1
        atm -= strike

    option0 = df_cycle.query('strike == %r' % strikes[atm]).iloc[0]
    option1 = df_all.query('date == %r & option_code == %r' % (
        date1, option0['option_code']
    )).iloc[0]

    return option0, option1


def get_cycle_strike2(df_all, date0, date1,
                      name0, close0, cycle0, strike0,
                      name1, close1, cycle1, strike1):
    """
    Get two options using cycle strike
    :param df_all:
    :param date0: pd.datetime
    :param name0: str ('CALL', 'PUT')
    :param close0: float
    :param cycle0: int
    :param strike0: int
    :param date1: pd.datetime
    :param name1: str ('CALL', 'PUT')
    :param close1: float
    :param cycle1: int
    :param strike1: int
    :return: set of pd.DataFrame
    """
    df_enter = df_all.query('date == %r & dte >= %r' % (date0, (date1 - date0).days))
    df_exit = df_all.query('date == %r' % date1)
    # print df_date.to_string(line_width=1000)

    cycles = np.sort(df_enter['dte'].unique())
    if cycle0 < 0 or cycle1 < 0:
        raise ValueError('Cycle value cannot be negative')
    elif cycle0 > len(cycles) or cycle1 > len(cycles):
        raise ValueError('Cycle is greater than cycle length')
    else:
        df_cycle0 = df_enter.query('dte == %r & name == %r' % (
            cycles[cycle0], name0
        )).sort_values('strike')
        df_cycle1 = df_enter.query('dte == %r & name == %r' % (
            cycles[cycle1], name1
        )).sort_values('strike')
        # print df_cycle.to_string(line_width=1000)

    strikes0 = np.sort(df_cycle0['strike'])
    atm0 = np.argmin(np.abs(strikes0 - close0))
    if name0 == 'CALL':
        if close0 > strikes0[atm0]:
            atm0 += 1
        atm0 += strike0
    elif name0 == 'PUT':
        if close0 < strikes0[atm0]:
            atm0 -= 1
        atm0 -= strike0
    strikes1 = np.sort(df_cycle1['strike'])
    atm1 = np.argmin(np.abs(strikes1 - close1))
    if name1 == 'CALL':
        if close1 > strikes1[atm1]:
            atm1 += 1
        atm1 += strike1
    elif name1 == 'PUT':
        if close1 < strikes1[atm1]:
            atm1 -= 1
        atm1 -= strike1

    enter0 = df_cycle0.query('strike == %r' % strikes0[atm0]).iloc[0]
    enter1 = df_cycle1.query('strike == %r' % strikes1[atm1]).iloc[0]
    exit0 = df_exit.query('date == %r & option_code == %r' % (
        date1, enter0['option_code']
    )).iloc[0]
    exit1 = df_exit.query('date == %r & option_code == %r' % (
        date1, enter1['option_code']
    )).iloc[0]

    return enter0, exit0, enter1, exit1
