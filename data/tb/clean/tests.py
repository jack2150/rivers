from django.core.urlresolvers import reverse

from base.tests import TestSetUp
from data.models import SplitHistory
from data.tb.clean import *
from data.tb.clean.split_new import CleanSplitNew
from data.tb.clean.split_old import CleanSplitOld
from rivers.settings import QUOTE


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
        db = pd.HDFStore(QUOTE)
        df_stock = db.select('stock/thinkback/%s' % symbol.lower())
        df_dividend = db.select('event/dividend/%s' % symbol.lower())
        db.close()

        df_rate = get_div_yield(df_stock, df_dividend)
        self.assertTrue(len(df_rate.query('amount > 0')))
        self.assertTrue(len(df_rate.query('div > 0')))
        self.assertListEqual(['amount', 'div'], list(df_rate.columns))

        print df_rate.query('div > 0').to_string(line_width=1000)


class TestCleanOptionClass(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'AIG'

        option_code = 'AIG140322C50'
        today = '140220'
        ex_date, name, strike = extract_code(option_code)
        # ex_date, name, strike, today, rf_rate, close, bid, ask, impl_vol=0.01, div=0.0

        self.data = {
            'ex_date': ex_date,
            'name': name,
            'strike': strike,
            'today': today,
            'rf_rate': 0.12,
            'close': 49.22,
            'bid': 0.78,
            'ask': 0.80,
            'impl_vol': 20.49,
            'div': 0.002540,
        }

        self.clean = OptionCalc(**self.data)

    def test_init(self):
        """
        All init property is correct
        """
        print 'after init...'

        self.assertEqual(self.clean.name, self.data['name'])
        self.assertEqual(self.clean.strike, self.data['strike'])

        self.assertEqual(type(self.clean.ex_date), Date)
        self.assertEqual(type(self.clean.today), Date)
        self.assertEqual(type(self.clean.settle), Date)

        self.assertEqual(self.clean.rate, self.data['rf_rate'] / 100.0)
        self.assertEqual(type(self.clean.rf_rate), FlatForward)
        self.assertEqual(type(self.clean.exercise), AmericanExercise)
        self.assertIn(self.clean.name, [Option.Call, Option.Put])
        self.assertEqual(type(self.clean.payoff), PlainVanillaPayoff)

        self.assertEqual(type(self.clean.underlying), SimpleQuote)
        self.assertEqual(self.clean.div, self.data['div'])
        self.assertEqual(type(self.clean.div_yield), FlatForward)

        self.assertEqual(self.clean.iv, self.data['impl_vol'] / 100.0)

        self.assertFalse(self.clean.ref_value)
        self.assertEqual(type(self.clean.time_step), long)
        self.assertEqual(type(self.clean.grid_point), long)

        self.assertEqual(self.clean.bid, self.data['bid'])
        self.assertEqual(self.clean.ask, self.data['ask'])

    def test_start_vanilla_option(self):
        """
        Test start vanilla option from quantlib
        """
        self.clean.volatility = None
        self.clean.process = None
        self.clean.option = None

        print 'run start_vanilla_option...'
        self.clean.start_vanilla_option()

        self.assertEqual(type(self.clean.volatility), BlackConstantVol)
        self.assertEqual(type(self.clean.process), BlackScholesMertonProcess)
        self.assertEqual(type(self.clean.option), VanillaOption)

    def test_start_black_calculator(self):
        """
        Test start black calculator from quantlib
        """
        self.clean.black_calc = None

        print 'run start_black_calculator...'
        self.clean.start_black_calculator()

        self.assertEqual(type(self.clean.black_calc), BlackCalculator)
        self.assertGreater(self.clean.term, 0)

    def test_impl_vol(self):
        """
        Test calculate implied volatility
        """
        print 'run impl_vol...'
        impl_vol = self.clean.impl_vol()

        print 'exact: %.2f, result: %.2f' % (self.data['impl_vol'], impl_vol * 100)
        self.assertEqual(type(impl_vol), float)
        self.assertAlmostEquals(round(impl_vol * 100, 2), self.data['impl_vol'], 0)

    def test_theo_price(self):
        """
        Test calculate implied volatility
        """
        print 'run theo_price...'
        theo_price = self.clean.theo_price()

        print 'exact: %.2f~%.2f, result: %.2f' % (
            self.data['ask'], self.data['bid'], theo_price
        )
        self.assertEqual(type(theo_price), float)
        self.assertTrue(self.data['bid'] <= theo_price <= self.data['ask'])

    def test_greek(self):
        """
        Test calculate greek: delta, gamma, theta, vega
        """
        print 'run greek...'
        delta, gamma, theta, vega = self.clean.greek()

        print 'delta: %.2f, result: %.2f' % (.40, delta)
        self.assertEqual(type(delta), float)
        self.assertAlmostEqual(.40, delta, 1)

        print 'gamma: %.2f, result: %.2f' % (.13, gamma)
        self.assertEqual(type(gamma), float)
        self.assertAlmostEqual(.13, gamma, 1)

        print 'theta: %.2f, result: %.2f' % (-.02, theta)
        self.assertEqual(type(theta), float)
        self.assertAlmostEqual(-.02, theta, 1)

        print 'vega: %.2f, result: %.2f' % (.05, vega)
        self.assertEqual(type(vega), float)
        self.assertAlmostEqual(.05, vega, 1)

    def test_prob(self):
        """
        Test calculate prob: itm, otm, touch
        """
        print 'run greek...'
        itm, otm, touch = self.clean.prob()

        print 'itm: %.2f, result: %.2f' % (37.71, itm)
        self.assertEqual(type(itm), float)
        self.assertAlmostEqual(37.71, itm, 0)

        print 'otm: %.2f, result: %.2f' % (62.29, otm)
        self.assertEqual(type(otm), float)
        self.assertAlmostEqual(62.29, otm, 0)

        print 'touch: %.2f, result: %.2f' % (77.92, touch)
        self.assertEqual(type(touch), float)
        self.assertAlmostEqual(77.92, touch, -1)

    def test_moneyness(self):
        """
        Test calculate moneyness intrinsic and extrinsic
        """
        print 'run moneyness...'
        intrinsic, extrinsic = self.clean.moneyness()

        print 'intrinsic: %.2f, result: %.2f' % (0, intrinsic)
        self.assertEqual(type(intrinsic), float)
        self.assertAlmostEqual(0, intrinsic, 0)

        print 'extrinsic: %.2f, result: %.2f' % (0.78, extrinsic)
        self.assertEqual(type(extrinsic), float)
        self.assertAlmostEqual(0.78, extrinsic, 0)


class TestCppCleanNormal(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'WFC'
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
        db = pd.HDFStore(QUOTE)
        df_split1 = db.select('option/%s/valid/split/new' % self.symbol.lower())
        df_split2 = db.select('option/%s/clean/split/new' % self.symbol.lower())
        df_split2 = df_split2.sort_values('date', ascending=False)
        df_stock = db.select('stock/thinkback/%s' % self.symbol.lower())
        df_stock = df_stock.reset_index()
        db.close()

        for new_code in df_split1['new_code'].unique():
            df_temp = df_split1.query('new_code == %r' % new_code)[[
                'ask', 'bid', 'date', 'ex_date', 'ex_month', 'ex_year',
                'last', 'mark', 'name', 'open_int', 'option_code', 'new_code', 'others',
                'right', 'special', 'strike', 'volume',
                'theo_price', 'impl_vol', 'delta', 'gamma', 'theta', 'vega',
                'prob_itm', 'prob_otm', 'prob_touch', 'dte', 'intrinsic', 'extrinsic'
            ]]
            print df_temp.to_string(line_width=1000)
            print df_split2.query('new_code == %r' % new_code).to_string(line_width=1000)

            print df_stock[df_stock['date'].isin(df_temp['date'])]


class TestCppCleanSplitOld(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'C'  # test with C
        self.clean_option = CleanSplitOld(self.symbol)

        self.split_history = SplitHistory(
            symbol=self.symbol,
            date='2011-05-09',
            fraction='1/10'
        )
        self.split_history.save()

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

    def test_clean_split_old_view(self):
        """
        Test raw option import for cli
        """
        self.client.get(reverse('admin:clean_split_old_h5', kwargs={'symbol': 'c'}))

    def test_verify_data(self):
        db = pd.HDFStore(QUOTE)
        df_split1 = db.select('option/%s/valid/split/old' % self.symbol.lower())
        df_split2 = db.select('option/%s/clean/split/old' % self.symbol.lower())
        df_split2 = df_split2.sort_values('date', ascending=False)
        db.close()

        for option_code in df_split1['option_code'].unique()[0:1]:
            df_temp = df_split1.query('option_code == %r' % option_code)[[
                'ask', 'bid', 'date', 'ex_date', 'ex_month', 'ex_year',
                'last', 'mark', 'name', 'open_int', 'option_code', 'others',
                'right', 'special', 'strike', 'volume',
                'theo_price', 'impl_vol', 'delta', 'gamma', 'theta', 'vega',
                'prob_itm', 'prob_otm', 'prob_touch', 'dte', 'intrinsic', 'extrinsic'
            ]]
            print df_temp.to_string(line_width=1000)
            print df_split2.query('option_code == %r' % option_code).to_string(line_width=1000)
