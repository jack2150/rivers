from glob import glob
import os
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.models import *
from rivers.settings import BASE_DIR


class TestData(TestSetUp):
    def tearDown(self):
        TestSetUp.tearDown(self)
        Stock.objects.all().delete()
        OptionContract.objects.all().delete()
        Option.objects.all().delete()

    def test_stock(self):
        """
        Test save symbol data using dict and output dataFrame
        """
        symbols = ('AAPL', 'AIG', 'BAC', 'C')

        data = [
            {'volume': 44525905, 'high': 130.63, 'low': 129.23, 'date': '2015-04-24', 'close': 130.28, 'open': 130.49},
            {'volume': 5894183, 'high': 57.17, 'low': 56.85, 'date': '2015-04-24', 'close': 56.99, 'open': 57.1},
            {'volume': 40766109, 'high': 15.75, 'low': 15.61, 'date': '2015-04-24', 'close': 15.64, 'open': 15.71},
            {'volume': 10150537, 'high': 53.22, 'low': 52.85, 'date': '2015-04-24', 'close': 52.89, 'open': 53.16},
        ]

        df = DataFrame()
        for symbol, stock_data in zip(symbols, data):
            stock = Stock()
            stock.symbol = symbol
            stock.load_dict(stock_data)
            stock.save()

            self.assertTrue(stock.id)
            df = df.append(stock.to_hdf())

        print df

    def test_option_contract(self, output=True):
        """
        Test option contract saving dict and output dataFrame
        """
        OptionContract.objects.all().delete()

        symbol = 'AAPL'
        data = [
            {'ex_month': 'MAY', 'right': '100', 'contract': 'CALL', 'option_code': 'AAPL150515C190', 'ex_year': 15,
             'others': '', 'strike': 190.0, 'special': 'Standard'},
            {'ex_month': 'MAY', 'right': '100', 'contract': 'PUT', 'option_code': 'AAPL150515P190', 'ex_year': 15,
             'others': '', 'strike': 190.0, 'special': 'Standard'},
            {'ex_month': 'MAY4', 'right': '100', 'contract': 'CALL', 'option_code': 'AAPL150522C95', 'ex_year': 15,
             'others': 'Weeklys', 'strike': 95.0, 'special': 'Weeklys'},
            {'ex_month': 'MAY4', 'right': '100', 'contract': 'PUT', 'option_code': 'AAPL150522P95', 'ex_year': 15,
             'others': 'Weeklys', 'strike': 95.0, 'special': 'Weeklys'}
        ]

        df = DataFrame()
        for contract_data in data:
            contract = OptionContract()
            contract.symbol = symbol
            contract.load_dict(contract_data)
            contract.save()

            self.assertTrue(contract.id)
            df = df.append(contract.to_hdf())

        if output:
            print df

    def test_option(self):
        """
        Test option saving dict and output dataFrame
        """
        self.test_option_contract(output=False)

        symbol = 'AAPL'
        data = [
            {'volume': 24.0, 'prob_otm': 8.49, 'last': 32.15, 'prob_itm': 91.51, 'bid': 32.3, 'open_int': 8077.0,
             'dte': 637, 'mark': 32.9, 'theo_price': 32.49, 'ask': 32.525, 'vega': 0.31, 'impl_vol': 13.93,
             'delta': -0.8, 'date': '2015-04-24', 'theta': -0.02, 'prob_touch': 25.74, 'intrinsic': 19.72,
             'extrinsic': 12.805, 'gamma': 0.01},
            {'volume': 17.0, 'prob_otm': 79.82, 'last': 9.7, 'prob_itm': 20.18, 'bid': 10.09, 'open_int': 3125.0,
             'dte': 637, 'mark': 10.35, 'theo_price': 10.0, 'ask': 10.025, 'vega': 0.59, 'impl_vol': 32.9,
             'delta': 0.34, 'date': '2015-04-24', 'theta': -0.01, 'prob_touch': 56.5, 'intrinsic': 0.0,
             'extrinsic': 10.025, 'gamma': 0.01}
        ]

        option_contract = OptionContract.objects.first()

        df = DataFrame()
        for option_data in data:
            option = Option()
            option.symbol = symbol
            option.date = '2015-04-24'
            option.option_contract = option_contract
            option.load_dict(option_data)
            option.save()

            self.assertTrue(option.id)
            df = df.append(option.to_hdf())

        print df.to_string(line_width=200)

    def test_dividend(self):
        """
        Test dividend saving csv and output dataFrame
        """
        lines = [
            'BCAR,$0.05,12/17/08,1/5/09,1/7/09,1/21/09',
            'CMCSA,$0.0625,12/10/08,1/5/09,1/7/09,1/28/09',
            'GNTX,$0.11,12/2/08,1/5/09,1/7/09,1/20/09',
        ]

        df = DataFrame()
        for line in lines:
            dividend = Dividend()
            dividend.load_csv(line)
            dividend.save()

            self.assertTrue(dividend.id)
            df = df.append(dividend.to_hdf())

        print df

    def test_earning(self):
        """
        Test earning saving csv line and output dataFrame
        """
        lines = [
            '11/17/09,,After Market,,UFEN.PK,Q3,,,Unconfirmed',
            '11/17/09,,Before Market,,VIT,Q3,0.14,0.14,Verified',
            '11/17/09,11/17/09,Before Market,1:10:00 AM CST,REMI.OB,Q2,-0.03,-0.04,Verified',
            '11/17/09,11/17/09,Before Market,5:00:00 AM CST,COV,Q4,0.699,0.11,Verified',
            '11/17/09,11/17/09,Before Market,5:01:00 AM CST,HD,Q3,0.353,0.41,Verified',
        ]

        df = DataFrame()
        for line in lines:
            earning = Earning()
            earning.load_csv(line)
            earning.save()
            print earning

            self.assertTrue(earning.id)
            df = df.append(earning.to_hdf())

        print df.to_string(line_width=200)

    def test_treasury_instrument(self, output=True):
        """
        Test load csv lines, save data and output dataFrame
        """
        lines = [
            '"Series Description","12-MONTH AUCTION HIGH BILL RATE BY ISSUE DATE"',
            '"Unit:","Percent:_Per_Year"',
            '"Multiplier:","1"',
            '"Currency:","NA"',
            '"Unique Identifier: ","H15/discontinued/H0.RIFSGFPIY01_N.A"',
            '"Time Period","H0.RIFSGFPIY01_N.A"',
        ]

        treasury_instrument = TreasuryInstrument()
        treasury_instrument.name = 'US Gov Security'
        treasury_instrument.instrument = 'Constant Maturity Nominal'
        treasury_instrument.maturity = '1 Year'
        treasury_instrument.time_frame = 'Annual'
        treasury_instrument.load_csv(lines)
        treasury_instrument.save()

        if output:
            df = treasury_instrument.to_hdf()
            print df.to_string(line_width=300)

        self.assertTrue(treasury_instrument.id)

    def test_treasury_interest(self):
        """
        Test treasury interest load csv, save data and outpu data frame
        """
        self.test_treasury_instrument(output=False)
        treasury_instrument = TreasuryInstrument.objects.first()

        time_frames = ['Annual', 'Monthly', 'Weekly', 'Bday']
        lines = ['2014,3.10', '1988-05,2.48', '1993-01-26,3.26', '2006-08-02,3.22']

        interest = Series()
        for time_frame, line in zip(time_frames, lines):
            print 'set data:', time_frame, line
            # set time frame
            treasury_instrument.time_frame = time_frame

            # set interest data
            treasury_interest = TreasuryInterest()
            treasury_interest.treasury = treasury_instrument
            treasury_interest.load_csv(line)
            treasury_interest.save()

            interest = interest.append(treasury_interest.to_hdf())
            self.assertTrue(treasury_interest.id)

        print '.' * 60
        print interest




















class TestDataImport(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)
        User.objects.create_superuser('root', 'a@a.a', '123456')
        self.client.login(username='root', password='123456')

    def tearDown(self):
        TestSetUp.tearDown(self)
        Stock.objects.all().delete()
        OptionContract.objects.all().delete()
        Option.objects.all().delete()

    def test_web_quote_import(self):
        """
        Test web import using google or yahoo into csv
        """
        self.skipTest("Only test when needed...")

        source = 'google'
        symbol = 'IWM'

        underlying = Underlying(symbol=symbol)
        underlying.start = '2015-05-20'
        underlying.save()

        print 'run web import view...'
        response = self.client.get(reverse('admin:web_quote_import', args=(source, symbol, )))

        print 'inserted stocks:'
        for stock in response.context['stocks']:
            print stock

        self.assertEqual(
            response.context['title'], '{source} Web Import: {symbol}'.format(
                source=source.capitalize(), symbol=symbol.upper())
        )
        self.assertLessEqual(len(response.context['stocks']), 11)

        stocks = Stock.objects.all()
        self.assertTrue(stocks.exists())

    def test_csv_quote_import(self):
        """
        Test csv import file into db
        """
        self.skipTest("Only test when needed...")

        symbol = 'AIG'

        underlying = Underlying(symbol=symbol)
        underlying.start = '2015-04-01'
        underlying.save()

        print 'run csv import view...'
        response = self.client.get(reverse('admin:csv_quote_import', args=(symbol, )))

        self.assertGreaterEqual(len(response.context['files']), 1)

        print 'stock count:', Stock.objects.count()
        print 'contract count:', OptionContract.objects.count()
        print 'option count', Option.objects.count()

        self.assertTrue(Stock.objects.count())
        self.assertTrue(OptionContract.objects.count())
        self.assertTrue(Option.objects.count())

        stocks = Stock.objects.all()
        # self.assertGreater(stocks.count(), 0)
        print 'stock count: %d' % Stock.objects.count()
        for stock in stocks[:5]:
            print stock
        else:
            print '...'
            print '.' * 60

        option_contracts = OptionContract.objects.all()
        # self.assertGreater(option_contracts.count(), 0)
        print 'option_contract count: %d' % option_contracts.count()

        for option_contract in option_contracts[:3]:
            print option_contract
        else:
            print '...'
            print '.' * 60

        options = Option.objects.all()
        #self.assertGreater(options.count(), 0)
        print 'options count: %d' % options.count()

        for option in options[:5]:
            print option
        else:
            print '...'
            print '.' * 60

    def test_daily_quote_import(self):
        """
        Test csv import file into db
        """
        year = '2015'
        date = '2015-04-24'
        symbols = ('AAPL', 'AIG', 'BAC', 'C')
        to_path = os.path.join(BASE_DIR, 'files', 'thinkback', '__daily__')
        for symbol in symbols:
            # create underlying
            underlying = Underlying(symbol=symbol)
            underlying.start = '2015-04-01'
            underlying.save()

            # move file into daily, then start save
            fname = '{date}-StockAndOptionQuoteFor{symbol}.csv'.format(date=date, symbol=symbol)
            from_path = os.path.join(BASE_DIR, 'files', 'thinkback', symbol.lower(), year)
            print '{fname} move file into __daily__ folder...'.format(fname=fname)
            os.rename(os.path.join(from_path, fname), os.path.join(to_path, fname))

        print 'run csv daily import view...'
        response = self.client.get(reverse('admin:daily_quote_import'))

        self.assertEqual(len(response.context['files']), 4)

        symbols = [s[0] for s in Stock.objects.all().values_list('symbol').distinct()]

        for symbol in symbols:
            print '.' * 100 + '\n' + symbol + '\n' + '.' * 100
            stock = Stock.objects.filter(symbol=symbol)

            df = DataFrame()
            for s in stock:
                df = df.append(s.to_hdf())

            print df
            self.assertEqual(stock.count(), 3)
            self.assertTrue(OptionContract.objects.exists())
            self.assertTrue(Option.objects.exists())

            print '.' * 100 + '\n'

        # check daily folder is empty
        self.assertFalse(len(glob(os.path.join(to_path, '*.csv'))))

    def test_csv_calendar_import(self):
        """
        Test import dividend using csv files from tos calendars
        """
        #self.skipTest("Only test when needed...")

        print 'run dividend import view...'
        response = self.client.get(reverse('admin:csv_calendar_import', args=('dividend',)))

        self.assertLessEqual(len(response.context['files']), 11)

        df = DataFrame()
        for dividend in Dividend.objects.all():
            df = df.append(dividend.to_hdf())
        print df.to_string(line_width=200)

        print 'dividend count:', Dividend.objects.count()

        self.assertGreater(Dividend.objects.count(), 100)

    def test_csv_earning_import(self):
        """
        Test import earning using csv files from tos calendars
        """
        print 'run earning import view...'
        response = self.client.get(reverse('admin:csv_calendar_import', args=('earning',)))
        self.assertLessEqual(len(response.context['files']), 11)

        df = DataFrame()
        for earning in Earning.objects.all():
            df = df.append(earning.to_hdf())
        print df.to_string(line_width=200)

        print 'earning count:', Earning.objects.count()

        self.assertGreater(Earning.objects.count(), 50)

    def test_treasury_import(self):
        """
        Test import treasury files into db
        """
        print 'run treasury import view...'
        response = self.client.get(reverse('admin:treasury_import'))

        treasury_instruments = TreasuryInstrument.objects.all()

        df_treasury = DataFrame()
        for treasury_instrument in treasury_instruments:
            df_treasury = df_treasury.append(treasury_instrument.to_hdf())

            self.assertGreaterEqual(treasury_instrument.treasuryinterest_set.count(), 10)

        print df_treasury.to_string(line_width=300)

        self.assertGreaterEqual(len(df_treasury), 8)















