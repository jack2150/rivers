import logging
import numpy as np

logger = logging.getLogger('views')


def get_price_ask(df_all, date0, date1, name, cycle, ask):
    """

    :param df_all:
    :param date0:
    :param date1:
    :param name: str ('CALL', 'PUT')
    :param cycle: int
    :param ask: float
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

    price_ask = np.sort(df_cycle['ask'])
    atm = np.argmin(np.abs(price_ask - ask))  # closest to zero is nearest

    option0 = df_cycle.query('ask == %r' % price_ask[atm]).iloc[0]
    option1 = df_all.query('date == %r & option_code == %r' % (
        date1, option0['option_code']
    )).iloc[0]

    return option0, option1

    # todo: need update