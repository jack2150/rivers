from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.models import Underlying
from data.plugin.raw.views import *
from rivers.settings import QUOTE


class TestCsvOptionH5X(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbols = [
            'AIG', 'FSLR', 'SNDK', 'DDD', 'BP', 'C', 'CELG',
            'YUM', 'XOM', 'WMT', 'WFC', 'VZ', 'TWTR', 'TSLA', 'PG',
            'DAL', 'DIS', 'EA', 'EBAY', 'FB'
        ]

    def test_read_file(self):
        """
        Test read thinkback file and get option data
        """
        symbol = self.symbols[0]
        db = pd.HDFStore(QUOTE)
        df_stock = db.select('stock/thinkback/%s' % symbol.lower())
        db.close()

        df_test = pd.concat([
            df_stock.head(10),
            df_stock.tail(10)
        ])

        keys, options = read_file(df_test, symbol.lower())

        print '\nkeys:'
        print pd.Series(keys)
        self.assertEqual(type(keys), list)
        self.assertTrue(len(keys))

        print '\noptions:'
        for i, option in enumerate(options):
            if i < 6:
                print option
            self.assertEqual(type(option), dict)
        self.assertTrue(len(options))

    def test_make_code2(self):
        """
        Test make new option code using contract data
        symbol, others, right, special, ex_date, name, strike, extra
        """
        date = pd.to_datetime

        samples = [
            {
                'symbol': 'AIG', 'others': '', 'right': '100', 'special': 'Standard',
                'ex_date': date('20140220'), 'name': 'CALL', 'strike': '57', 'extra': '',
            },
            {
                'symbol': 'WFC', 'others': 'US$ 25.23', 'right': '19/100', 'special': 'Standard',
                'ex_date': date('20090116'), 'name': 'PUT', 'strike': '4', 'extra': '',
            },
            {
                'symbol': 'C', 'others': 'CWS 53; US$ 6.1', 'right': '100', 'special': 'Standard',
                'ex_date': date('20100521'), 'name': 'CALL', 'strike': '22', 'extra': '',
            },
            {
                'symbol': 'SNDK', 'others': '', 'right': '100', 'special': 'Weeklys',
                'ex_date': date('20150717'), 'name': 'PUT', 'strike': '59.5', 'extra': '3',
            }
        ]

        expects = ['AIG140220C57', 'WFC1090116P4', 'C2100521C22', 'SNDK3150717P59.5']

        for sample, expect in zip(samples, expects):
            print pd.DataFrame([sample])

            new_code = make_code2(**sample)
            print 'result: %s\n' % new_code
            self.assertEqual(new_code, expect)

    def test_change_code(self):
        """
        Test change code using existing option code
        """
        samples = [
            {
                'symbol': 'AIG', 'code': 'IKG100320C45',
                'others': '', 'right': '100', 'special': 'Standard'
            },
            {
                'symbol': 'WFC', 'code': 'WFC090116P4',
                'others': 'US$ 25.23', 'right': '100', 'special': 'Standard'
            },
            {
                'symbol': 'C', 'code': 'CS2100521C22',
                'others': '', 'right': '25/100', 'special': 'Weeklys'
            },
            {
                'symbol': 'SNDK', 'code': 'SNDK3150717P59.5',
                'others': 'CWS 53; US$ 6.1', 'right': '100', 'special': 'Standard'
            }
        ]
        expects = ['AIG100320C45', 'WFC1090116P4', 'C12100521C22', 'SNDK23150717P59.5']

        for sample, expect in zip(samples, expects):
            print pd.DataFrame([sample])

            new_code = change_code(**sample)
            print 'result: %s\n' % new_code
            self.assertEqual(new_code, expect)

    def test_valid_option2(self):
        """
        Test valid raw option data from csv
        """
        indexes = range(10)
        bids = [0.1, 1.35, 0.7, 22.8, 9.64, 0.95, 7.18, 34, 0.25, 3.5]
        asks = [0.15, 1.5, 0.9, 24, 10.5, 1.2, 7.5, 36, 0.35, 4.5]
        volumes = [6, 0, 42, 99, 45, 81, 663, 932, 12, 391, 21, 14]
        open_ints = [100, 951, 2019, 649, 1107, 1181, 437, 2341, 121, 214]
        dtes = [121, 333, 0, 14, 9, 81, 650, 75, 63, 62]

        results = valid_option2(
            indexes, bids, asks, volumes, open_ints, dtes
        )

        print 'run valid_option2...'
        print 'results: %s' % results
        self.assertTrue(np.all(results))

        bids[0] = -1
        asks[1] = -1
        bids[2] = 0.95
        volumes[3] = -100
        open_ints[4] = -2
        dtes[5] = -1

        results = valid_option2(
            indexes, bids, asks, volumes, open_ints, dtes
        )

        print 'results: %s' % results
        self.assertTrue(np.count_nonzero(results) == 4)

    # noinspection PyShadowingNames
    def test_valid_contract2(self):
        """
        Test valid contract detail
        """
        ex_months = ['MAY1', 'JUL', 'DEC2', 'FEB4', 'AUG', 'MAR3']
        ex_years = [13, 11, 16, 9, 14, 12]
        rights = ['100', '19/100', '25/100', '50/100', '200', '150']
        specials = ['Standard', 'Weeklys', 'Standard', 'Quarterlys', 'Mini', 'Weeklys']

        print 'run valid_contract2...'
        results = valid_contract2(ex_months, ex_years, rights, specials)
        print 'results: %s' % results
        self.assertTrue(np.all(results))

        ex_months[0] = 'MAY7'
        ex_years[1] = '-1'
        rights[2] = 'AAA'
        specials[3] = 'Monthly'

        results = valid_contract2(ex_months, ex_years, rights, specials)
        print 'results: %s' % results
        self.assertEqual(np.count_nonzero(results), 2)

    def test_get_contract(self):
        """
        Test get contract from first row of dataframe
        """
        df_test = pd.DataFrame(
            {'open_int': {0: 0.0}, 'right': {0: '100'}, 'others': {0: ''}, 'theo_price': {0: 0.0},
             'ex_date': {0: pd.Timestamp('2009-01-16 00:00:00')}, 'special': {0: 'Standard'},
             'impl_vol': {0: 0.0}, 'extrinsic': {0: 0.015}, 'option_code': {0: 'AIG090116P95'},
             'mark': {0: 93.325}, 'strike': {0: 95.0}, 'theta': {0: 0.0}, 'missing': {0: 0},
             'bid': {0: 93.25}, 'volume': {0: 0.0}, 'expire': {0: True}, 'ex_year': {0: 9},
             'delta': {0: 0.0}, 'ask': {0: 93.40}, 'last': {0: 0.0}, 'intrinsic': {0: 93.31},
             'ex_month': {0: 'JAN'}, 'prob_otm': {0: 0.0}, 'prob_itm': {0: 100.0},
             'name': {0: 'PUT'}, 'dte': {0: 14}, 'vega': {0: 0.0}, 'prob_touch': {0: 1.78},
             'gamma': {0: 0.0}}
        )

        print 'run get_contract...'
        result = get_contract(df_test)

        print result
        self.assertEqual(result['ex_month'], 'JAN')
        self.assertEqual(result['ex_year'], 9)
        self.assertEqual(result['name'], 'PUT')
        self.assertEqual(result['option_code'], 'AIG090116P95')
        self.assertEqual(result['others'], '')
        self.assertEqual(result['right'], '100')
        self.assertEqual(result['special'], 'Standard')
        self.assertEqual(result['strike'], 95)

    def test_check_date(self):
        """
        Test check single option_code date is unique
        """
        symbol = self.symbols[0]

        db = pd.HDFStore(QUOTE)
        df_option = db.select('option/%s/raw/data' % symbol.lower())
        db.close()

        df_test = df_option[-10:].reset_index()

        print 'run check_date with valid date...'
        check_date(df_test)
        print 'everything ok'

        df_test2 = pd.concat([df_test, df_test])
        """:type: pd.DataFrame"""
        print 'run check_date with invalid date...'
        self.assertRaises(lambda: check_date(df_test2))
        print 'error raise'

    def test_check_code(self):
        """
        Test check option_code is old format and without symbol
        """
        symbol = self.symbols[0]
        option_code = 'AIG090116P95'
        contract = {
            'right': '100', 'others': '', 'ex_date': pd.Timestamp('2009-01-16 00:00:00'),
            'special': 'Standard', 'option_code': 'AIG090116P95',
            'strike': 95.0, 'ex_year': 9, 'ex_month': 'JAN', 'name': 'PUT'
        }

        print 'run check_code...'
        new_code = check_code(symbol, contract)
        print 'old code: %s, new code: %s' % (contract['option_code'], new_code)
        self.assertEqual(contract['option_code'], new_code)

        print '\n' + '-' * 100 + '\n'

        print 'run check_code with old format option_code...'
        contract['option_code'] = 'AILET'
        new_code = check_code(symbol, contract)
        print 'old code: %s, new code: %s' % (contract['option_code'], new_code)
        self.assertNotEqual(contract['option_code'], new_code)
        self.assertEqual(option_code, new_code)

        print '\n' + '-' * 100 + '\n'

        print 'run check_code with no symbol option_code...'
        contract['option_code'] = 'LKS090116P95'
        new_code = check_code(symbol, contract)
        print 'old code: %s, new code: %s' % (contract['option_code'], new_code)
        self.assertNotEqual(contract['option_code'], new_code)
        self.assertEqual(option_code, new_code)

    def test_set_missing(self):
        symbol = self.symbols[0]

        db = pd.HDFStore(QUOTE)
        df_stock = db.select('stock/thinkback/%s' % symbol.lower())
        df_contract = db.select('option/%s/raw/contract' % symbol.lower())
        df_option = db.select('option/%s/raw/data' % symbol.lower())
        db.close()

        df_option = df_option.reset_index()
        df_contract['missing'] = set_missing(df_contract, df_option, df_stock.index)

        df_missing = df_contract[df_contract['missing'] > 0]
        print df_missing.to_string(line_width=1000)
        self.assertGreater(len(df_missing), 0)

    def test_mass_csv_option_h5x(self):
        """
        Test csv option import into h5 db after csv stock import
        some of the csv can be wrong, for example fslr 08-25-2011 got wrong cycle info
        """
        # self.skipTest('Only test when need!')
        print 'run mass csv option import 2...'

        db = pd.HDFStore(QUOTE)
        for symbol in self.symbols:
            self.underlying = Underlying(
                symbol=symbol,
                start='2009-01-01',
                stop='2016-01-01'
            )
            self.underlying.save()
            # self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': symbol}))
            # self.client.get(reverse('admin:csv_option_h5x', kwargs={'symbol': symbol}))
            df = db.select('option/%s/raw/contract' % symbol.lower())
            print symbol, df['right'].unique()

        db.close()

    def test_csv_option_h5x(self):
        """
        Test csv option import into h5 db after csv stock import
        some of the csv can be wrong, for example fslr 08-25-2011 got wrong cycle info
        """
        symbol = self.symbols[0]

        # self.skipTest('Only test when need!')
        print 'run csv stock import view...', symbol
        self.underlying = Underlying(
            symbol=symbol,
            start='2009-01-01',
            stop='2016-01-01'
        )
        self.underlying.save()

        self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': symbol}))
        self.client.get(reverse('admin:csv_option_h5x', kwargs={'symbol': symbol.lower()}))

        db = pd.HDFStore(QUOTE)
        df_contract = db.select('option/%s/raw/contract' % symbol.lower())
        df_option = db.select('option/%s/raw/data' % symbol.lower())
        db.close()

        print 'df_contract: %d' % len(df_contract)
        print 'df_option: %d' % len(df_option)

    def test_both_raw_csv_equal(self):
        """
        Test old and new import by contract and option size
        """
        print 'total symbols:', len(self.symbols)
        symbol = self.symbols[-4].lower()

        db = pd.HDFStore(QUOTE)
        df_contract0 = db.select('option/%s/raw/contract' % symbol)
        df_option0 = db.select('option/%s/raw/data' % symbol)
        db.close()
        print 'old', len(df_contract0), len(df_option0)

        db = pd.HDFStore('quote2.h5')
        df_contract1 = db.select('option/%s/raw/contract' % symbol)
        df_option1 = db.select('option/%s/raw/data' % symbol)
        db.close()
        print 'new', len(df_contract1), len(df_option1)

        if len(df_contract0) == len(df_contract1) and len(df_option0) == len(df_option1):
            print 'all same'
        else:
            diff = np.setdiff1d(
                df_contract0['option_code'],
                df_contract1['option_code']
            )
            if len(diff) == 0:
                assert len(df_contract0['option_code'].unique()) == len(df_contract1['option_code'])
                print 'contract same length, some duplicate contract in old'
            else:
                print diff

            codes1 = list(df_contract1['option_code'])
            for i, code0 in enumerate(diff):
                print i, code0,
                if code0 in codes1:
                    df0 = df_option0.query('option_code == %r' % code0)
                    df1 = df_option1.query('option_code == %r' % code0)
                    length0 = len(df0)
                    length1 = len(df1)

                    if length0 != length1:
                        print 'found but different length'
                        print length0, length1, length0 == length1
                        print df_contract0.query('option_code == %r' % code0)
                        print df0.to_string(line_width=1000)
                        print df_contract1.query('option_code == %r' % code0)
                        print df1.to_string(line_width=1000)
                        print '*' * 200
                        exit()
                else:
                    print 'not found on new'
                    print df_contract0.query('option_code == %r' % code0).to_string(line_width=1000)

                    df0 = df_option0.query('option_code == %r' % code0)
                    df1 = df_option1.query('option_code == %r' % code0)

                    print 'old got:', len(df0), 'new got:', len(df1)
                    print df0.to_string(line_width=1000)
                    print df1.to_string(line_width=1000)
                    print '*' * 200
                print ''
