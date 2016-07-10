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
    if name == 'CALL' and close > strikes[atm]:
        atm += 1
    elif name == 'PUT' and close < strikes[atm]:
        atm -= 1

    i = atm + strike if name == 'CALL' else atm - strike
    option0 = df_cycle.query('strike == %r' % strikes[i]).iloc[0]
    option1 = df_all.query('date == %r & option_code == %r' % (
        date1, option0['option_code']
    )).iloc[0]

    return option0, option1


def get_cycle_strike2(df_all, date0, date1, name, close, cycle, strike, wide):
    """

    :param wide:
    :param df_all:
    :param date0:
    :param date1:
    :param name: str ('CALL', 'PUT')
    :param close: float
    :param cycle: int
    :param strike: int
    :return:
    """
    if wide < 1:
        raise ValueError('Wide range must greater than 0')

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

    option_a0 = df_cycle.query('strike == %r' % strikes[atm + strike]).iloc[0]
    option_b0 = df_cycle.query('strike == %r' % strikes[atm + strike + wide]).iloc[0]
    option_a1 = df_all.query('date == %r & option_code == %r' % (
        date1, option_a0['option_code']
    )).iloc[0]
    option_b1 = df_all.query('date == %r & option_code == %r' % (
        date1, option_b0['option_code']
    )).iloc[0]

    return option_a0, option_a1, option_b0, option_b1
