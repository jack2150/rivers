import numpy as np
from django.core.urlresolvers import reverse
from base.dj_tests import TestSetUp
from base.utests import TestUnitSetUp
from data.models import SplitHistory
from data.tb.clean import *
from data.tb.clean.split_new import CleanSplitNew
from data.tb.clean.split_old import CleanSplitOld
from data.tb.fillna.calc import extract_code
from rivers.settings import QUOTE_DIR


class TestCleanOptionMethod(TestSetUp):
    def test_extract_code(self):
        """
        Test extra ex_date, name and strike from option code
        """
        codes = ['AILAZ', 'AJU100220C65', 'AIG100220P7', 'AIG140228C52.5', 'AIG1110122P5']
        ex_dates = ['', '100220', '100220', '140228', 0]
        names = ['', 1, -1, 1, 0]
        strikes = ['', 65, 7, 52.5, 0]

        for code, ex_date0, name0, strike0 in zip(codes, ex_dates, names, strikes):
            print code,

            if code == 'AILAZ':
                self.assertRaises(lambda: extract_code(code))
                print 'correct raise error'
            else:
                ex_date1, name1, strike1 = extract_code(code)
                print 'result', ex_date1, name1, strike1
                self.assertEqual(ex_date0, ex_date1)
                self.assertEqual(name0, name1)
                self.assertEqual(strike0, strike1)

    def test_get_div_yield(self):
        """
        Test get dividend yield
        """
        symbol = 'AIG'
        db = pd.HDFStore(os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower()))
        df_stock = db.select('stock/thinkback')
        df_dividend = db.select('event/dividend')
        db.close()

        df_rate = get_div_yield(df_stock, df_dividend)
        self.assertTrue(len(df_rate.query('amount > 0')))
        self.assertTrue(len(df_rate.query('div > 0')))
        self.assertListEqual(['amount', 'div'], list(df_rate.columns))

        print df_rate.query('div > 0').to_string(line_width=1000)


class TestCppCleanNormal(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'TZA'
        self.clean_option = CleanNormal(self.symbol)

    def test_get_merge_data(self):
        """
        Test get_merge_data form db
        """
        self.clean_option.get_merge_data()

        print self.clean_option.df_all.head().to_string(line_width=1000)
        self.assertEqual(type(self.clean_option.df_all), pd.DataFrame)
        self.assertGreater(len(self.clean_option.df_all), 1)

    def test_to_csv(self):
        """
        Test df_all with extra column to csv lines
        593,2009-01-16,2009-01-16,CALL,55.0,0.43,0.0,0.0,0.05,0.0,0.0
        """
        self.clean_option.get_merge_data()
        lines = self.clean_option.to_csv()

        self.assertGreater(len(lines), 1)
        for line in lines.split():
            print line
            data = line.split(',')
            self.assertEqual(len(data), 11)

    def test_save_clean(self):
        """
        :return:
        """
        lines = """
        ,theo_price,impl_vol,delta,gamma,theta,vega,prob_itm,prob_otm,prob_touch,dte,intrinsic,extrinsic
        0,15,1.6,0.98,0.0062,-0.08,0.003,0.97,0.032,0.064,3,15,0.08
        1,9.2,0,-1.$,1.$,-1.$,-1.$,1,0,0,38,9.2,0
        2,0.25,0.26,0.1,0.035,-0.012,0.036,0.089,0.91,0.18,38,0,0.26
        3,7.2,0,-1.$,1.$,-1.$,-1.$,1,0,0,38,7.2,0
        4,0.24,0.27,0.097,0.032,-0.012,0.034,0.083,0.92,0.17,38,0,0.25
        5,7.7,0,-1.$,1.$,-1.$,-1.$,1,0,0,38,7.7,0
        6,0.096,0.23,0.051,0.023,-0.0064,0.021,0.044,0.96,0.088,38,0,0.11
        7,8.2,0,-1.$,1.$,-1.$,-1.$,1,0,0,38,8.2,0
        8,0.26,0.3,0.096,0.028,-0.013,0.034,0.08,0.92,0.16,38,0,0.26
        9,8.7,0,-1.$,1.$,-1.$,-1.$,1,0,0,38,8.7,0
        """
        self.clean_option.get_merge_data()
        self.clean_option.save_clean(lines)


class TestCppCleanSplitNew(TestSetUp):
    def setUp(self):
        """
        Primary test DDD, LULU, BIDU
        """
        TestSetUp.setUp(self)

        self.symbol = 'DDD'
        self.clean_option = CleanSplitNew(self.symbol)

    def test_get_merge_data(self):
        """
        Test get_merge_data form db
        """
        self.clean_option.get_merge_data()

        print self.clean_option.df_all.head().to_string(line_width=1000)
        self.assertEqual(type(self.clean_option.df_all), pd.DataFrame)
        self.assertGreater(len(self.clean_option.df_all), 1)

    def test_clean_split_new_view(self):
        """
        Test raw option import for cli
        """
        self.client.get(reverse('admin:clean_split_new_h5', kwargs={'symbol': 'ddd'}))

    def test_verify_data(self):
        db = pd.HDFStore(os.path.join(CLEAN_DIR, '__%s__.h5' % self.symbol.lower()))
        df_split1 = db.select('option/valid/split/new')
        df_split2 = db.select('option/clean/split/new')
        df_split2 = df_split2.sort_values('date', ascending=False)
        df_stock = db.select('stock/thinkback')
        df_stock = df_stock.reset_index()
        db.close()

        for new_code in df_split1['new_code'].unique():
            df_temp = df_split1.query('new_code == %r' % new_code)[[
                'ask', 'bid', 'date', 'ex_date', # 'ex_month', 'ex_year',
                'last', 'mark', 'name', 'open_int', 'option_code', 'new_code', 'others',
                'right', 'special', 'strike', 'volume',
                'theo_price', 'impl_vol', 'delta', 'gamma', 'theta', 'vega',
                'prob_itm', 'prob_otm', 'prob_touch', 'dte', 'intrinsic', 'extrinsic'
            ]]
            print df_temp.to_string(line_width=1000)
            print df_split2.query('new_code == %r' % new_code).to_string(line_width=1000)

            print df_stock[df_stock['date'].isin(df_temp['date'])]

