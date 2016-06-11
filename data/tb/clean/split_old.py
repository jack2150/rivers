import os
import pandas as pd
from fractions import Fraction
from StringIO import StringIO
from data.models import Underlying, SplitHistory
from data.tb.clean import get_quote_data
from rivers.settings import CLEAN_DIR


class CleanSplitOld(object):
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
        try:
            df_split0 = db.select('option/valid/split/old')
            df_split0 = df_split0.reset_index(drop=True)
        except KeyError:
            raise LookupError('No data for df_split/old')
        db.close()

        self.merge_option_data(df_split0, df_div, df_rate, df_stock)

    def merge_option_data(self, df_split0, df_div, df_rate, df_stock):
        """

        :param df_split0:
        :param df_div:
        :param df_rate:
        :param df_stock:
        :return:
        """
        # merge all into a single table
        df_all = pd.merge(df_split0, df_stock.reset_index(), how='inner', on=['date'])
        df_all = pd.merge(df_all, df_rate.reset_index(), how='inner', on=['date'])
        self.df_all = pd.merge(df_all, df_div.reset_index(), how='inner', on=['date'])

    def update_split_date(self):
        """
        update split_history date right into new right
        :return:
        """
        # update right
        split_history = SplitHistory.objects.filter(symbol=self.symbol.upper())

        for s in split_history:
            self.df_all.loc[self.df_all['date'] == s.date, 'right'] = s.fraction

        # update close price
        self.df_all['multiply'] = self.df_all['right'].apply(
            lambda r: float(Fraction(r)) if '/' in r else 1
        )
        self.df_all['close1'] = self.df_all['close'] * self.df_all['multiply']

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
        # using close1 (price before split) instead of close
        df_temp = df_temp[[
            'ex_date2', 'date2', 'name', 'strike', 'rate', 'close1', 'bid', 'ask', 'impl_vol2', 'div'
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
            db.remove('option/clean/split/old')
        except KeyError:
            pass
        db.append('option/clean/split/old', df_clean)
        db.close()

    def convert_data(self, lines):
        """

        :param lines:
        :return:
        """
        df_result = pd.read_csv(StringIO(''.join(lines)), index_col=0)
        # remove invalid greek
        for key in ('delta', 'gamma', 'theta', 'vega'):
            df_result[key] = df_result[key].astype('float')
            df_result[key] += 0
        df_raw = self.df_all[[
            'ask', 'bid', 'date', 'ex_date', # 'ex_month', 'ex_year',
            'last', 'mark', 'name', 'open_int', 'option_code', 'others',
            'right', 'special', 'strike', 'volume'
        ]]
        df_clean = pd.concat([df_raw, df_result], axis=1)
        """:type: pd.DataFrame"""
        return df_clean

    def update_underlying(self):
        """
        Update underlying after completed
        """
        underlying = Underlying.objects.get(symbol=self.symbol.upper())
        underlying.log += 'Clean df_split/old, symbol: %s length: %d\n' % (
            self.symbol.upper(), len(self.df_all)
        )
        underlying.save()
