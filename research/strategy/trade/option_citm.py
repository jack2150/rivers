import logging
import numpy as np

logger = logging.getLogger('views')


def get_prob_itm(df_all, date0, date1, name, cycle, itm):
    """

    :param df_all:
    :param date0:
    :param date1:
    :param name: str ('CALL', 'PUT')
    :param close: float
    :param cycle: int
    :param itm: float
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

    prob_itm = np.sort(df_cycle['prob_itm'])
    atm = np.argmin(np.abs(prob_itm - itm))  # closest to zero is nearest

    option0 = df_cycle.query('prob_itm == %r' % prob_itm[atm]).iloc[0]
    option1 = df_all.query('date == %r & option_code == %r' % (
        date1, option0['option_code']
    )).iloc[0]

    return option0, option1

# todo: need update