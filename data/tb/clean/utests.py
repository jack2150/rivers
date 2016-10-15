from base.ufunc import ts
from base.utests import TestUnitSetUp

import numpy as np
from django.core.urlresolvers import reverse
from data.models import SplitHistory
from data.tb.clean import *
from data.tb.clean.split_new import CleanSplitNew
from data.tb.clean.split_old import CleanSplitOld
from data.tb.fillna.calc import extract_code
from rivers.settings import QUOTE_DIR


class TestCppCleanSplitOld(TestUnitSetUp):
    def setUp(self):
        """
        Primary test C, AIG, TZA
        """
        TestUnitSetUp.setUp(self)

        self.symbol = 'C'
        self.clean_option = CleanSplitOld(self.symbol)

    def test_update_split_date(self):
        """
        Test get_merge_data form db
        """
        self.clean_option.get_merge_data()
        print 'run update_split_date...'
        self.clean_option.update_split_date()

        df_all = self.clean_option.df_all
        # noinspection PyTypeChecker
        same = np.count_nonzero(df_all['close'] == df_all['close1'])
        self.assertNotEqual(len(df_all), same)
        print 'df_all close: %d' % len(df_all)
        print 'df_all close != close1: %d' % same

        code = df_all['option_code'].unique()[0]
        print df_all[df_all['option_code'] == code].to_string(line_width=1000)

    def test_to_csv(self):
        """
        Test df_all with extra column to csv lines
        593,2009-01-16,2009-01-16,CALL,55.0,0.43,0.0,0.0,0.05,0.0,0.0
        2011-02-24
        3/1, 5/1?????
        """
        self.clean_option.get_merge_data()
        # self.clean_option.df_all = self.clean_option.df_all[
        #     self.clean_option.df_all['option_code'] == 'TZA1120121C9'
        # ]
        self.clean_option.update_split_date()
        # ts(self.clean_option.df_all[['ask', 'bid', 'date', 'right', 'strike', 'close', 'close1']])
        lines = self.clean_option.to_csv()

        self.assertGreater(len(lines), 1)
        for line in lines.split():
            print line
            data = line.split(',')
            self.assertEqual(len(data), 12)

    def test_clean_split_old_view(self):
        """
        Test raw option import for cli
        """
        self.client.get(reverse('admin:clean_split_old_h5', kwargs={'symbol': 'c'}))

    def test_verify_data(self):
        db = pd.HDFStore(os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower()))
        df_stock = db.select('stock/thinkback').reset_index()
        db.close()

        db = pd.HDFStore(os.path.join(CLEAN_DIR, '__%s__.h5' % self.symbol.lower()))
        df_split1 = db.select('option/valid/split/old')
        df_split2 = db.select('option/clean/split/old')
        df_split2 = df_split2.sort_values('date', ascending=False)
        print 'df_split2: %d' % len(df_split2)
        db.close()

        print 'df_split1: %d' % len(df_split1)

        closes = df_stock[['date', 'close']]
        for option_code in df_split1['option_code'].unique()[:1]:
            df_temp = df_split1.query('option_code == %r' % option_code)[[
                'ask', 'bid', 'date', 'ex_date',  # 'ex_month', 'ex_year',
                'last', 'mark', 'name', 'open_int', 'option_code', 'others',
                'right', 'special', 'strike', 'volume',
                'theo_price', 'impl_vol', 'delta', 'gamma', 'theta', 'vega',
                'prob_itm', 'prob_otm', 'prob_touch', 'dte', 'intrinsic', 'extrinsic'
            ]]
            # print df_temp.to_string(line_width=1000)
            ts(pd.merge(df_temp, closes, on='date'))
            df_code = df_split2.query('option_code == %r' % option_code)
            ts(pd.merge(df_code, closes, on='date'))

