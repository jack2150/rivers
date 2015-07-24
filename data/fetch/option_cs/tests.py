from base.utests import TestUnitSetUp
from django.db.models.query import QuerySet
from quantitative.models import Algorithm


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