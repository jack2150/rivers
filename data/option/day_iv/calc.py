import os
import numpy as np
import pandas as pd
from data.option.day_iv.day_iv import DayImplVolStatic
from rivers.settings import QUOTE_DIR


def today_iv(df_iv, date, dte):
    """
    Using exact range expr method to calc some dte iv
    :param df_iv: pd.DataFrame
    :param date: str, Datetime, pd.Datetime
    :param dte: int
    """
    df = df_iv.query('date == %r' % date)

    iv_class = DayImplVolStatic()
    x = np.array(df['dte'])
    y = np.array(df['impl_vol'])
    d0, d1, x, y = iv_class.reduce_samples(dte, x, y)

    dte_iv = iv_class.range_expr(x, y, dte, False)
    dte_iv = dte_iv * np.sqrt(dte/365.0)

    return dte_iv


def correct_prob(x, name):
    """
    Set norm.cdf into correct probability
    :param x: dict
    :param name: str
    :return: float
    """
    return (1 - x['%s%%' % name] if x[name] > x['stock'] else x['%s%%' % name]) * 100
