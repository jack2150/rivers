from base.utests import TestUnitSetUp
from django.db.models.query import QuerySet
from quantitative.models import Algorithm
from simulation.models import Strategy
from simulation.strategy.single.single import *


class TestStrategyLongCall(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'BAC'
        self.algorithm = Algorithm.objects.get(rule='Options Day to Expire')
        #self.algorithm = Algorithm.objects.get(rule='EWMA change direction - H')

        self.quant = self.algorithm.make_quant()
        self.quant.seed_data(self.symbol)
        self.hd_args = {'dte': 45}
        self.cs_args = {'side': 'buy'}
        #self.hd_args = {'span': 60, 'previous': 20}
        #self.cs_args = {'holding': 20}

        self.strategy = Strategy.objects.get(name='Long Call by Cycle Strike')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }

    def test_make_order(self):
        """
        Test trade using stop loss order
        import profile
        # profile.runctx('self.strategy.make_order(
        df_stock, df_signal, expire=expire, **self.args)', globals(), locals())
        """
        df_stock = self.quant.handle_data(self.quant.data[self.symbol], **self.hd_args)
        df_signal = self.quant.create_signal(df_stock, **self.cs_args)

        print 'symbol:', self.symbol
        for expire in (False, True):
            print 'expire set:', expire

            df_order = self.strategy.make_order(df_stock, df_signal, expire=expire, **self.args)
            df_order['diff'] = df_order['stock0'] - df_order['strike']

            print df_order.to_string(line_width=300)

            pct_chg = df_order['pct_chg']
            pct_chg = pct_chg[pct_chg < 10]
            print pct_chg.sum(), np.round(pct_chg.mean(), 2),
            print np.round(float(pct_chg[pct_chg > 0].count() / float(pct_chg.count())), 2),
            print np.round(float(pct_chg[pct_chg < 0].count() / float(pct_chg.count())), 2)

            print '-' * 100 + '\n'


class TestGetSingleOption(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbol = 'AIG'

        self.algorithm = Algorithm.objects.get(rule='Options Day to Expire')
        # self.algorithm = Algorithm.objects.get(rule='EWMA change direction - H')

        self.quant = self.algorithm.make_quant()
        self.quant.seed_data(self.symbol)
        self.hd_args = {'dte': 45}
        self.cs_args = {'side': 'buy'}

        df_stock = self.quant.handle_data(self.quant.data[self.symbol], **self.hd_args)
        self.df_signal = self.quant.create_signal(df_stock, **self.cs_args)

        self.dates0 = self.df_signal['date0']

    def test_get_options_by_cycle_strike(self):
        """
        Test get options by cycle and strike return valid DataFrame
        """
        names = ('CALL', 'PUT')
        moneyness = ('ITM', 'OTM')
        dte = 44
        cycle = 0
        strike = 0

        for name in names:
            for money in moneyness:
                print 'name: ', name, ' moneyness: ', money
                dates, options = get_options_by_cycle_strike(
                    symbol=self.symbol,
                    name=name,
                    dates0=self.dates0,
                    dte=dte,
                    moneyness=money,
                    cycle=cycle,
                    strike=strike
                )

                self.assertEqual(type(options), QuerySet)
                self.assertTrue(options.count())

                for date, (index, signal) in zip(dates, self.df_signal.iterrows()):
                    if date:
                        option0 = options.get(date=date)
                        print signal['date0'], '->', date, signal['close0'], option0, option0.dte

                        self.assertEqual(option0.contract.symbol, self.symbol)
                        self.assertEqual(option0.contract.name, name)
                        self.assertGreaterEqual(option0.dte, dte)

                print '-' * 100 + '\n'

    def test_get_option_by_contract_date(self):
        """
        Test get option by contract and date
        """
        contract = OptionContract.objects.filter(symbol=self.symbol).first()
        """:type: OptionContract"""

        date = contract.option_set.last().date

        date1, option1 = get_option_by_contract_date(contract, date)
        print option1

        self.assertEqual(option1.contract, contract)
        self.assertEqual(type(option1), Option)
        self.assertEqual(option1.date, date1)


class TestStrategyLongPut(TestStrategyLongCall):
    def setUp(self):
        TestStrategyLongCall.setUp(self)

        self.strategy = Strategy.objects.get(name='Long Put by Cycle Strike')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }


class TestStrategyNakedCall(TestStrategyLongCall):
    def setUp(self):
        TestStrategyLongCall.setUp(self)

        self.strategy = Strategy.objects.get(name='Naked Call by Cycle Strike')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }


class TestStrategyNakedPut(TestStrategyLongCall):
    def setUp(self):
        TestStrategyLongCall.setUp(self)

        self.strategy = Strategy.objects.get(name='Naked Put by Cycle Strike')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }


# todo: seed data can use date range