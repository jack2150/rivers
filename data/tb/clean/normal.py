import os
import pandas as pd
from StringIO import StringIO
from data.models import Underlying
from data.tb.fillna.calc import get_div_yield
from rivers.settings import QUOTE_DIR, CLEAN_DIR, TREASURY_DIR


def get_quote_data(symbol):
    """
    Get ready to use quote data for cleaning
    :param symbol: str
    :return: tuple of pd.DataFrame
    """
    path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
    db = pd.HDFStore(path)
    df_stock = db.select('stock/thinkback')
    df_stock = df_stock[['close']]
    treasury = pd.HDFStore(TREASURY_DIR)
    df_rate = treasury.select('RIFLGFCY01_N_B')  # series
    treasury.close()

    try:
        df_dividend = db.select('event/dividend')
        df_div = get_div_yield(df_stock, df_dividend)
    except KeyError:
        df_div = pd.DataFrame()
        df_div['date'] = df_stock.index
        df_div['amount'] = 0.0
        df_div['div'] = 0.0
    db.close()

    df_stock = df_stock.reset_index()
    df_rate = df_rate.reset_index()

    return df_div, df_rate, df_stock


class CleanNormal(object):
    def __init__(self, symbol):
        self.symbol = symbol.lower()
        self.df_all = pd.DataFrame()

        self.path = os.path.join(CLEAN_DIR, '__%s__.h5' % self.symbol)
        self.output = '%-6s | %-30s | %-s'

    def get_merge_data(self):
        """
        Merge df_all data with stock close, risk free rate and div yield
        """
        df_div, df_rate, df_stock = get_quote_data(self.symbol)

        db = pd.HDFStore(self.path)
        df_normal = db.select('option/valid/normal')
        df_normal = df_normal.reset_index(drop=True)
        db.close()

        self.merge_option_data(df_normal, df_div, df_rate, df_stock)

    def merge_option_data(self, df_normal, df_div, df_rate, df_stock):
        """
        Merge all option data into df_all that ready for clean
        :param df_div: pd.DataFrame
        :param df_normal: pd.DataFrame
        :param df_rate: pd.DataFrame
        :param df_stock: pd.DataFrame
        """
        # merge all into a single table
        df_all = pd.merge(df_normal, df_stock, how='inner', on=['date'])
        df_all = pd.merge(df_all, df_rate, how='inner', on=['date'])
        self.df_all = pd.merge(df_all, df_div.reset_index(), how='inner', on=['date'])

    def to_csv(self):
        """
        Format ex_date, date and impl_vol then output csv lines
        :return: list of str
        """
        df_temp = self.df_all.copy()
        """:type: pd.DataFrame"""
        df_temp['date2'] = df_temp['date'].apply(lambda d: d.date().strftime('%Y-%m-%d'))
        df_temp['ex_date2'] = df_temp['ex_date'].apply(lambda d: d.date().strftime('%Y-%m-%d'))
        df_temp['impl_vol2'] = df_temp['impl_vol'].apply(lambda iv: round(iv / 100.0, 2))
        df_temp = df_temp[[
            'ex_date2', 'date2', 'name', 'strike', 'rate', 'close', 'bid', 'ask', 'impl_vol2', 'div'
        ]]

        return df_temp.to_csv(header=False)

    def save_clean(self, lines):
        """
        Get result lines data from clean.exe that save into db
        :param lines: list of str
        """
        df_clean = self.convert_data(lines)

        # save data
        db = pd.HDFStore(self.path)
        try:
            db.remove('option/clean/normal')
        except KeyError:
            pass
        db.append('option/clean/normal', df_clean)
        db.close()

    def convert_data(self, lines):
        """
        Convert lines data into dataframe
        :param lines: list of str
        :return: pd.DataFrame
        """
        df_result = pd.read_csv(StringIO(''.join(lines)), index_col=0)
        # remove invalid greek
        for key in ('delta', 'gamma', 'theta', 'vega'):
            df_result[key] = df_result[key].astype('float')
            df_result[key] += 0

        df_raw = self.df_all[[
            'ask', 'bid', 'date', 'ex_date',  # 'ex_month', 'ex_year',
            'last', 'mark', 'name', 'open_int', 'option_code', 'others',
            'right', 'special', 'strike', 'volume'
        ]]
        df_clean = pd.concat([df_raw, df_result], axis=1)
        """:type: pd.DataFrame"""

        # reduce day
        df_clean['dte'] -= 1

        return df_clean

    def update_underlying(self):
        """
        Update underlying after completed
        """
        underlying = Underlying.objects.get(symbol=self.symbol.upper())
        underlying.log += 'Clean df_normal, symbol: %s length: %d\n' % (
            self.symbol.upper(), len(self.df_all)
        )
        underlying.save()
