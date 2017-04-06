import os
import pandas as pd
import numpy as np
from rivers.settings import QUOTE_DIR


class GetData(object):
    @staticmethod
    def get_stock_data(symbol, reindex=False):
        """
        :param symbol: str
        :param reindex: bool
        :return: pd.DataFrame
        """
        path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
        db = pd.HDFStore(path)
        try:
            df_stock = db.select('/stock/google/')
            """:type: pd.DataFrame"""
        except KeyError:
            try:
                df_stock = db.select('/stock/yahoo/')
                """:type: pd.DataFrame"""
            except KeyError:
                raise KeyError('No df_stock data')

        db.close()

        if reindex:
            index = pd.date_range(start=df_stock.index.min(), end=df_stock.index.max(), name='date')
            df_stock = df_stock.reindex(index)
            df_stock = df_stock.fillna(method='pad')
            df_stock = df_stock.sort_index(ascending=False)

        return df_stock

    @staticmethod
    def get_event_data(symbol, event):
        """

        :param symbol: str
        :param event: str
        :return:
        """
        path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
        db = pd.HDFStore(path)
        try:
            df_event = db.select('/event/%s' % event.lower())
            """:type: pd.DataFrame """
        except KeyError:
            raise KeyError('No df_even data')
        db.close()

        return df_event

    @staticmethod
    def get_iv_data(symbol, dte):
        """

        :param symbol: str
        :param dte: int (30, 60, 90, 150, 365)
        :return:
        """
        path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
        db = pd.HDFStore(path)
        try:
            df_iv = db.select('/option/iv/day')
            df_iv = df_iv[df_iv['dte'] == dte]
        except KeyError:
            raise KeyError('No df_iv data')
        db.close()

        return df_iv

    @staticmethod
    def calc_day_iv(iv, dte, days):
        """

        :param iv: float
        :param dte: int
        :param days: int
        :return:
        """
        return round(np.sqrt(iv * 2 / 252 * dte / days), 2)
