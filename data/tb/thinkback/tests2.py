import os
from pprint import pprint
import pandas as pd
from glob import glob
from base.tests import TestSetUp
from data.tb.thinkback.thinkback import ThinkBack, CALL_NAMES
from rivers.settings import THINKBACK_DIR


class TestThinkBack(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'NFLX'
        self.year = '2015'

        self.dir_name = os.path.join(
            THINKBACK_DIR, self.symbol.lower(), self.year
        )

        self.fpaths = list()
        for path in glob(os.path.join(self.dir_name, '*.csv')):
            # if '2009-07-01' in path:
            #    self.fpaths.append(path)
            self.fpaths.append(path)

        self.thinkback = None

    def test_get_stock(self):
        """
        Test get stock data
        """
        self.thinkback = ThinkBack(fpath=self.fpaths[0])
        stock = self.thinkback.get_stock()

        pprint(stock)

        self.assertEqual(type(stock['date']), pd.tslib.Timestamp)
        self.assertEqual(type(stock['last']), float)
        self.assertEqual(type(stock['net_change']), float)
        self.assertEqual(type(stock['volume']), int)
        self.assertEqual(type(stock['open']), float)
        self.assertEqual(type(stock['high']), float)
        self.assertEqual(type(stock['low']), float)

    def test_get_cycles2(self):
        """
        Test get cycle for all format
        """
        sample = [
            '16 JAN 10  (11)  100',
            '20 FEB 10  (46)  100 (Weeklys)',
            '20 MAR 10  (74)  100 (Mini)',
            '19 JUN 10  (165)  100',
            '22 JAN 11  (382)  100 (Quarterlys)',
            '21 JAN 12  (746)  20/100 ',
            '2 MAR 13  (4)  150 (Weeklys)',
            '18 JUL 09  (142)  100 (US$ 25.23)',
            '16 JAN 10  (324)  19/100 (US$ 3616.11)',
            '18 JUL 09  (142)  100 (Weeklys) (US$ 25.23)',
            '18 JUL 09  (142)  100 (CDL 25.23)',
        ]
        self.thinkback = ThinkBack(fpath=self.fpaths[0])
        self.thinkback.lines = sample
        cycles = self.thinkback.get_cycles()

        df = pd.DataFrame(cycles)
        print df.to_string(line_width=1000)

    def test_get_cycles_files(self):
        """
        Test get cycle using open file
        """
        cycles = []
        for fpath in self.fpaths:
            # print 'open path: %s' % fpath
            self.thinkback = ThinkBack(fpath=fpath)

            # print 'run get_cycles...'
            cycles += self.thinkback.get_cycles()

        print 'output using dataframe...'
        df = pd.DataFrame(cycles)
        print df.to_string(line_width=1000)

    def test_get_cycle_options(self):
        """
        Test get cycle option from lines
        """
        columns = CALL_NAMES
        columns.append('dte')
        columns.append('date')

        for fpath in self.fpaths:
            self.thinkback = ThinkBack(fpath=fpath)

            cycles = self.thinkback.get_cycles()

            for cycle in cycles:
                options = self.thinkback.get_cycle_options(cycle)
                # pprint(options)

                for contract, option in options:
                    print contract
                    print option

                    self.assertEqual(type(contract), dict)
                    self.assertEqual(type(contract['others']), str)

                    self.assertEqual(type(contract['right']), str)  # not int, str

                    self.assertEqual(type(contract['name']), str)
                    self.assertIn(contract['name'], ['CALL', 'PUT'])

                    self.assertEqual(type(contract['special']), str)
                    self.assertIn(contract['special'], ['Weeklys', 'Standard', 'Mini', 'Quarterlys'])

                    self.assertEqual(type(contract['strike']), float)
                    self.assertGreater(contract['strike'], 0)

                    self.assertEqual(type(contract['option_code']), str)

                    for key in option.keys():
                        self.assertIn(key, columns)
                        if key == 'dte':
                            self.assertEqual(type(option['dte']), int)
                        elif key not in ('date', 'option_code'):
                            self.assertEqual(type(option[key]), float)
                        elif key == 'option_code':
                            self.assertEqual(type(option['option_code']), str)
                        else:
                            self.assertEqual(type(option['date']), pd.tslib.Timestamp)

    def test_custom(self):
        """
        Testing for some bug only
        """
        symbol = 'GOOG'
        date = '2014-04-02'
        fpath = os.path.join(
            THINKBACK_DIR, symbol.lower(), date[:4],
            '%s-StockAndOptionQuoteFor%s.csv' % (date, symbol)
        )

        tb = ThinkBack(fpath=fpath)
        stocks = tb.get_stock()
        options = tb.get_options()

        import pandas
        df = pandas.DataFrame(options)
        print df.to_string(line_width=1000)
        print df['dte'].unique()
