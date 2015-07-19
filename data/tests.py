from django.contrib.auth.models import User
from base.tests import TestSetUp
from data.views import *
from rivers.settings import BASE_DIR


class TestData(TestSetUp):
    def tearDown(self):
        TestSetUp.tearDown(self)

        for stock in Stock.objects.all():
            stock.delete()

        for contract in OptionContract.objects.all():
            contract.delete()

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
            {'ex_month': 'MAY', 'right': '100', 'name': 'CALL', 'option_code': 'AAPL150515C190', 'ex_year': 15,
             'others': '', 'strike': 190.0, 'special': 'Standard'},
            {'ex_month': 'MAY', 'right': '100', 'name': 'PUT', 'option_code': 'AAPL150515P190', 'ex_year': 15,
             'others': '', 'strike': 190.0, 'special': 'Standard'},
            {'ex_month': 'MAY4', 'right': '100', 'name': 'CALL', 'option_code': 'AAPL150522C95', 'ex_year': 15,
             'others': 'Weeklys', 'strike': 95.0, 'special': 'Weeklys'},
            {'ex_month': 'MAY4', 'right': '100', 'name': 'PUT', 'option_code': 'AAPL150522P95', 'ex_year': 15,
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
            option.contract = option_contract
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

        try:
            treasury_instrument.save()
        except IntegrityError:
            print 'already exists...'

        if output:
            df = treasury_instrument.to_hdf()
            print df.to_string(line_width=300)

        self.assertTrue(treasury_instrument.id)

    def test_treasury_interest(self):
        """
        Test treasury interest load csv, save data and outpu data frame
        """
        TreasuryInstrument.objects.all().delete()
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
        if not User.objects.filter(username='root').count():
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

    def test_event_import(self):
        """
        Test import dividend using csv files from tos calendars
        """
        self.skipTest("Only test when needed...")

        print 'run dividend import view...'
        response = self.client.get(reverse('admin:event_import', args=('dividend',)))

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
        self.skipTest("Only test when needed...")

        print 'run earning import view...'
        response = self.client.get(reverse('admin:event_import', args=('earning',)))
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
        self.skipTest("Only test when needed...")

        print 'run treasury import view...'
        self.client.get(reverse('admin:treasury_import'))

        treasury_instruments = TreasuryInstrument.objects.all()

        df_treasury = DataFrame()
        for treasury_instrument in treasury_instruments:
            df_treasury = df_treasury.append(treasury_instrument.to_hdf())

            self.assertGreaterEqual(treasury_instrument.treasuryinterest_set.count(), 10)

        print df_treasury.to_string(line_width=300)

        self.assertGreaterEqual(len(df_treasury), 8)


class TestTruncateSymbol(TestSetUp):
    def test_truncate_symbol_form(self):
        """
        Test truncate symbol form
        """
        symbol = 'AIG'
        path = os.path.join(BASE_DIR, 'files', 'thinkback', symbol.lower(), '2015')
        fpath = glob(os.path.join(path, '*.csv'))[0]
        stock_data, option_data = ThinkBack(fpath).read()

        # save stock
        stock = Stock()
        stock.symbol = symbol
        stock.source = 'thinkback'
        stock.load_dict(stock_data)
        stock.save()

        for contract_dict, option_dict in option_data:
            # save contract
            contract = OptionContract()
            contract.symbol = symbol
            contract.source = 'tos_thinkback'
            contract.load_dict(contract_dict)
            contract.save()

            # save option
            option = Option()
            option.contract = contract
            option.load_dict(option_dict)
            option.save()

        self.assertTrue(Stock.objects.filter(symbol=symbol).count())
        self.assertTrue(OptionContract.objects.filter(symbol=symbol).count())
        self.assertTrue(Option.objects.count())

        # do web import
        #self.client.get(reverse('admin:web_quote_import', args=('google', symbol, )))
        #self.client.get(reverse('admin:web_quote_import', args=('yahoo', symbol, )))

        print 'run form truncate data...'
        form = TruncateSymbolForm(data={
            'symbol': 'AIG'
        })
        self.assertTrue(form.is_valid())
        form.truncate_data()

        self.assertFalse(Stock.objects.filter(symbol=symbol).count())
        self.assertFalse(OptionContract.objects.filter(symbol=symbol).count())
        self.assertFalse(Option.objects.count())

        print 'all record have been removed...'

    def test_truncate_symbol_view(self):
        """
        Test truncate symbol view
        """
        symbol = 'AIG'
        underlying = Underlying(symbol=symbol)
        underlying.start = '2015-05-20'
        underlying.stop = '2015-05-30'
        underlying.thinkback = 213
        underlying.google = 321
        underlying.yahoo = 123
        underlying.save()

        response = self.client.get(reverse('admin:truncate_symbol', kwargs={'symbol': symbol}))

        stats = response.context['stats']

        for key1 in ('thinkback', 'google', 'yahoo'):
            print stats[key1]
            self.assertIn(key1, stats.keys())

            for key2 in ('stock', 'start', 'stop'):
                self.assertIn(key2, stats[key1])

            if key1 == 'thinkback':
                self.assertIn('contract', stats[key1])
                self.assertIn('option', stats[key1])

        # test redirect and underlying set into 0
        response2 = self.client.post(
            reverse('admin:truncate_symbol', kwargs={'symbol': symbol}),
            data={'symbol': symbol}
        )

        self.assertIn(
            reverse('admin:data_underlying_changelist'),
            response2.url
        )
        self.assertEqual(response2.status_code, 302)

        underlying = Underlying.objects.get(symbol=symbol)
        self.assertFalse(underlying.thinkback)
        self.assertFalse(underlying.google)
        self.assertFalse(underlying.yahoo)


class TestCsvImport(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)
        self.symbol = 'DIS'
        self.underlying = Underlying(symbol=self.symbol)
        self.underlying.start = '2010-01-01'
        self.underlying.stop = '2010-12-31'
        self.underlying.save()

    def tearDown(self):
        TestSetUp.tearDown(self)
        self.underlying.delete()

        for stock in Stock.objects.all():
            stock.delete()

    def test_csv_stock_import_view(self):
        """
        Test import thinkback csv stock into db
        :return:
        """
        print 'run csv stock import view...'
        response = self.client.get(
            reverse('admin:csv_stock_import', kwargs={'symbol': self.symbol})
        )

        print '\n' + 'missing dates:'
        for missing_date in response.context['missing_dates']:
            print missing_date

        print '\n' + 'completed files:'
        for completed_file in response.context['completed_files']:
            print completed_file

        stats = response.context['stats']
        print '\n' + 'stats:', stats
        self.assertGreater(stats['count'], 5)
        self.assertTrue(stats['start'])
        self.assertTrue(stats['stop'])

        stocks = Stock.objects.filter(symbol=self.symbol)
        self.assertGreater(stocks.count(), 5)

    def test_change_code(self):
        """
        Test change duplicated code in option contract table
        """
        data = dict(
            ex_month='JAN2',
            ex_year=13,
            right=100,
            special='Weeklys',
            strike=33.0,
            name='CALL',
            option_code='FSLR130111C34',
            others='',
            symbol='FSLR',
            source='thinkback'
        )
        contract0 = OptionContract(**data)
        contract0.expire = True
        contract0.save()

        contract1 = OptionContract(**data)
        self.assertGreater(contract0.id, 0)
        self.assertEqual(contract0.option_code, 'FSLR130111C34')
        self.assertFalse(contract1.code_change)

        change_code(contract1, data)

        # update again
        contract0 = OptionContract.objects.get(id=contract0.id)
        print 'contract0', contract0.option_code, contract0.code_change
        self.assertTrue(contract0.code_change)
        self.assertTrue(contract0.id)
        self.assertIn('FSLR130111C34_', contract0.option_code)
        print 'contract1', contract1.option_code, contract1.code_change
        self.assertFalse(contract1.code_change)
        self.assertTrue(contract1.id)
        self.assertEqual(contract1.option_code, 'FSLR130111C34')

    def test_get_contracts(self):
        """
        Test get contracts for a single symbol
        """
        for strike, forfeit in ((35.0, False), (36.0, True)):
            contract = OptionContract(
                ex_month='JAN2',
                ex_year=13,
                right=100,
                special='Weeklys',
                strike=strike,
                name='CALL',
                option_code='BAC130111C%d' % strike,
                others='',
                symbol='BAC',
                source='thinkback',
                forfeit=forfeit
            )
            contract.save()

        for error, expect in ((False, 1), (True, 2)):
            contracts = get_contracts(symbol='BAC', error=error)
            print contracts.__str__() + '\n'
            self.assertEqual(contracts.count(), expect)
            self.assertEqual(type(contracts), pd.Series)

    def test_get_dte_date(self):
        """
        Test dte date using ex_month and ex_year
        """
        calendar.setfirstweekday(calendar.SUNDAY)
        test_values = list()
        for ex_year in range(9, 16):
            for i, ex_month in [(i, calendar.month_abbr[i].upper()) for i in range(1, 13)]:
                week_count = 1
                for week in calendar.monthcalendar(ex_year, i):
                    if week[5]:
                        test_values.append(('%s%d' % (ex_month, week_count), ex_year))
                        week_count += 1

        for ex_month, ex_year in test_values:
            print ex_month, ex_year,
            date = get_dte_date(ex_month, ex_year)
            print date

            self.assertEqual(type(date), datetime.date)

    def test_csv_option_import_view(self):
        """
        Test import thinkback csv option into db
        """
        print 'run csv stock import view...'
        self.client.get(reverse('admin:csv_stock_import', kwargs={'symbol': self.symbol}))
        self.assertTrue(Stock.objects.count())

        print 'run csv option import view...'
        response1 = self.client.get(
            reverse('admin:csv_option_import', kwargs={'symbol': self.symbol})
        )

        # check view context
        for missing_date in response1.context['missing_dates']:
            datetime.datetime.strptime(missing_date['date'], '%m/%d/%y')
            self.assertEqual(type(missing_date['date']), str)
            self.assertGreater(missing_date['count'], 0)

        for contract in response1.context['forfeit_contracts']:
            self.assertEqual(type(contract), OptionContract)
            self.assertTrue(contract.id)
            self.assertTrue(contract.forfeit)

        self.assertIn('stats', response1.context)
        stats = response1.context['stats']

        contract_keys = (
            'count', 'expire', 'split', 'code_change', 'missing',
            'others', 'others_set', 'special', 'special_set'
        )
        for key in contract_keys:
            self.assertIn(key, response1.context['stats']['contracts'])

        self.assertIn('count', response1.context['stats']['options'])

        # check import result
        print 'contracts'
        print 'count:', stats['contracts']['count']
        print 'expired:', stats['contracts']['expire']
        print 'split:', stats['contracts']['split']
        print 'code_change:', stats['contracts']['code_change']
        print 'others:', stats['contracts']['others']
        print 'others_set:', stats['contracts']['others_set']
        print 'special:', stats['contracts']['special']
        print 'special_set:', stats['contracts']['special_set']
        print 'missing:', stats['contracts']['missing']

        print 'options'
        print 'count:', stats['options']['count']

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

        contracts = Option.objects.all()
        # self.assertGreater(options.count(), 0)
        print 'options count: %d' % contracts.count()

        for option in contracts[:5]:
            print option
        else:
            print '...'
            print '.' * 60


class TestUnderlyingManage(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'AIG'

        try:
            self.underlying = Underlying.objects.get(symbol=self.symbol)
        except ObjectDoesNotExist:
            self.underlying = Underlying(symbol=self.symbol)
            self.underlying.start = '2015-04-01'
            self.underlying.stop = '2015-04-30'
            self.underlying.save()

    def test_set_underlying(self):
        """
        Test set_underlying_updated view
        """
        for action in ('updated', 'validated'):
            print action
            self.assertFalse(getattr(self.underlying, action))
            print 'underlying before:', getattr(self.underlying, action)

            response = self.client.get(reverse(
                'admin:set_underlying', kwargs={
                    'symbol': self.symbol.lower(), 'action': action
                })
            )

            # check redirect
            self.assertIn(
                reverse('admin:data_underlying_changelist'),
                response.url
            )
            self.assertEqual(response.status_code, 302)

            self.underlying = Underlying.objects.get(symbol=self.symbol)
            self.assertTrue(getattr(self.underlying, action))
            print 'underlying updated:', getattr(self.underlying, action), '\n'
