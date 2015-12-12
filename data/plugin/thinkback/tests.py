from calendar import month_name
from datetime import datetime
from glob import glob
import os
from pandas import DataFrame
from base.tests import TestSetUp
from data.plugin.thinkback.thinkback import ThinkBack
from rivers.settings import BASE_DIR


class TestThinkBack(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'AIG'
        self.year = '2009'

        self.dir_name = os.path.join(
            BASE_DIR, 'files', 'thinkback', self.symbol.lower(), self.year
        )

        self.fpaths = list()
        for path in glob(os.path.join(self.dir_name, '*.csv')):
            if '2009-07-01' in path:
                self.fpaths.append(path)

        self.thinkback = None

    def test_get_cycles(self):
        """
        Test get cycle on every top of option chain section
        """
        test_date = '2009-07-01'
        for fpath in self.fpaths:
            if test_date in fpath:
                print fpath
                self.thinkback = ThinkBack(fpath=fpath)

                cycles = self.thinkback.get_cycles()
                self.assertEqual(type(cycles), list)

                for cycle in cycles:
                    print cycle['data']
                    self.assertEqual(type(cycle), dict)

                    self.assertEqual(len(cycle['data']), 5)
                    self.assertEqual(type(cycle['dte']), int)
                    self.assertGreaterEqual(cycle['dte'], 0)
                    self.assertEqual(type(cycle['line']), str)
                    self.assertGreater(cycle['start'], 10)
                    self.assertLess(cycle['start'], cycle['stop'])

    def test_get_cycle_options(self):
        """
        Test get cycle options from option chain
        """
        months = [month_name[i + 1][:3].upper() for i in range(12)]

        contract_keys = [
            'ex_month', 'ex_year', 'right', 'special', 'others',
            'strike', 'name', 'option_code'
        ]

        option_keys = [
            'date', 'dte',
            'bid', 'ask', 'last', 'mark', 'delta', 'gamma', 'theta', 'vega',
            'theo_price', 'impl_vol', 'prob_itm', 'prob_otm', 'prob_touch', 'volume',
            'open_int', 'intrinsic', 'extrinsic'
        ]

        df_contract = DataFrame()
        df_options = DataFrame()
        for fpath in self.fpaths[:1]:
            self.thinkback = ThinkBack(fpath=fpath)

            cycles = self.thinkback.get_cycles()
            for cycle in cycles:
                # print 'cycle: %s' % cycle['data']
                options = self.thinkback.get_cycle_options(cycle)

                for contract, option in options:
                    print contract,
                    print option

                    self.assertEqual(type(contract), dict)
                    self.assertEqual(sorted(contract.keys()), sorted(contract_keys))
                    self.assertEqual(type(contract['others']), str)

                    self.assertEqual(type(contract['ex_month']), str)
                    self.assertIn(contract['ex_month'][:3], months)
                    if len(contract['ex_month']) == 4:
                        self.assertGreater(int(contract['ex_month'][3]), 0)
                        self.assertLessEqual(int(contract['ex_month'][3]), 12)

                    self.assertEqual(type(contract['ex_year']), int)
                    self.assertGreater(contract['ex_year'], 0)
                    self.assertLessEqual(contract['ex_year'], 99)

                    self.assertEqual(type(contract['right']), str)  # not int, str

                    self.assertEqual(type(contract['name']), str)
                    self.assertIn(contract['name'], ['CALL', 'PUT'])

                    self.assertEqual(type(contract['special']), str)
                    self.assertIn(contract['special'], ['Weeklys', 'Standard', 'Mini', 'Quarterlys'])

                    self.assertEqual(type(contract['strike']), float)
                    self.assertGreater(contract['strike'], 0)

                    self.assertEqual(type(contract['option_code']), str)

                    for key in option.keys():
                        self.assertIn(key, option_keys)
                        if key == 'date':
                            self.assertEqual(type(option['date']), str)
                            self.assertTrue(datetime.strptime(option['date'], '%Y-%m-%d'))
                        elif key == 'dte':
                            self.assertEqual(type(option['dte']), int)
                        else:
                            self.assertEqual(type(option[key]), float)

        print df_contract

        print df_options.to_string(line_width=300)

    def test_custom(self):
        """
        Testing for some bug only
        """
        symbol = 'AIG'
        date = '2014-05-01'
        fpath = os.path.join(
            BASE_DIR, 'files', 'thinkback', symbol.lower(), date[:4],
            '%s-StockAndOptionQuoteFor%s.csv' % (date, symbol)
        )

        tb = ThinkBack(fpath=fpath)
        stocks, options = tb.read()

        for o in options:
            if o[0]['option_code'] in ('AIG160115C95', 'AIG160115P95'):
                print o[0]['option_code']
