import os
import pandas as pd
from StringIO import StringIO
from data.models import Underlying
from data.tb.clean import get_quote_data
from rivers.settings import CLEAN_DIR


class CleanSplitNew(object):
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
            df_split1 = db.select('option/valid/split/new')
            df_split1 = df_split1.reset_index(drop=True)
        except KeyError:
            raise LookupError('No data for df_split/new')
        db.close()

        # merge all into a single table
        df_all = pd.merge(df_split1, df_stock.reset_index(), how='inner', on=['date'])
        df_all = pd.merge(df_all, df_rate.reset_index(), how='inner', on=['date'])
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
        df_result = pd.read_csv(StringIO(''.join(lines)), index_col=0)

        # remove invalid greek
        for key in ('delta', 'gamma', 'theta', 'vega'):
            df_result[key] = df_result[key].astype('float')
            df_result[key] += 0

        df_raw = self.df_all[[
            'ask', 'bid', 'date', 'ex_date', 'ex_month', 'ex_year',
            'last', 'mark', 'name', 'open_int', 'option_code', 'new_code', 'others',
            'right', 'special', 'strike', 'volume'
        ]]

        df_clean = pd.concat([df_raw, df_result], axis=1)
        """:type: pd.DataFrame"""

        # save data
        db = pd.HDFStore(self.path)
        try:
            db.remove('option/clean/split/new')
        except KeyError:
            pass
        db.append('option/%s/clean/split/new', df_clean)
        db.close()

    def update_underlying(self):
        """
        Update underlying after completed
        """
        underlying = Underlying.objects.get(symbol=self.symbol.upper())
        underlying.log += 'Clean df_split/new, symbol: %s length: %d\n' % (
            self.symbol.upper(), len(self.df_all)
        )
        underlying.save()
