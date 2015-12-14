from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.plugin.clean import *
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

        self.clean = CleanOption(**self.data)

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


class TestCleanOptionView(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'AIG'

    # noinspection PyUnresolvedReferences
    def test_mass_extract_codes(self):
        """
        Test extract data from a list of option_code
        """
        db = pd.HDFStore(QUOTE)
        df_contract = db.select('option/%s/raw/contract' % self.symbol.lower())
        db.close()

        option_codes = pd.concat([
            df_contract['option_code'].head(10),
            df_contract['option_code'].tail(10)
        ]).reset_index(drop=True)

        print 'used option_codes:'
        print option_codes

        results = mass_extract_codes(option_codes)

        print '\nresult:'
        print pd.DataFrame({
            'ex_date': results[0],
            'name': results[1],
            'strike': results[2],
        })

        for ex_date, name, strike in zip(results[0], results[1], results[2]):
            self.assertEqual(type(ex_date), str)
            self.assertIn(name, [-1, 1])
            self.assertEqual(type(strike), np.float64)

    def test_clean_option(self):
        """
        Test clean option view with multi process loop
        """
        # self.client.get(reverse('admin:clean_option', kwargs={'symbol': self.symbol.lower()}))
        self.client.get(reverse('admin:clean_option', kwargs={
            'symbol': self.symbol.lower(), 'core': 8
        }))

        db = pd.HDFStore(QUOTE)
        df_contract = db.select('option/%s/clean/contract' % self.symbol.lower())
        df_option = db.select('option/%s/clean/data' % self.symbol.lower())
        db.close()

        print df_contract.head(10).to_string(line_width=1000)
        print df_option.head(10).to_string(line_width=1000)
