from calendar import month_name
from datetime import datetime
from glob import glob
import os
from base.tests import TestSetUp
from data.io.thinkback import ThinkBack
from data.models import *
from rivers.settings import BASE_DIR


class TestThinkBack(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'AIG'
        self.year = '2015'

        self.dir_name = os.path.join(
            BASE_DIR, 'files', 'thinkback', self.symbol.lower(), self.year
        )

        self.fpaths = list()
        for path in glob(os.path.join(self.dir_name, '*.csv')):
            self.fpaths.append(path)

        self.thinkback = None

    def test_stock(self):
        """
        Test open thinkback csv and save into stock
        """
        expected_keys = ['date', 'volume', 'open', 'high', 'low', 'last', 'net_change']

        df = DataFrame()
        for fpath in self.fpaths:
            self.thinkback = ThinkBack(fpath=fpath)

            data = self.thinkback.get_stock()

            self.assertEqual(type(data), dict)
            for key, value in data.items():
                self.assertIn(key, expected_keys)

            # save stock
            stock = Stock()
            stock.symbol = self.symbol
            stock.load_dict(data)
            stock.save()

            self.assertTrue(stock.id)
            df = df.append(stock.to_hdf())

        print df

    def test_get_cycles(self):
        for fpath in self.fpaths[:1]:
            self.thinkback = ThinkBack(fpath=fpath)

            cycles = self.thinkback.get_cycles()
            self.assertEqual(type(cycles), list)

            for cycle in cycles:
                print cycle
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
            'strike', 'contract', 'option_code'
        ]

        option_keys = [
            'date', 'dte',
            'last', 'mark', 'bid', 'ask', 'delta', 'gamma', 'theta', 'vega',
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
                    #print 'current contract, option code: %s' % contract['option_code']
                    #pprint(contract, width=400)

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

                    self.assertEqual(type(contract['contract']), str)
                    self.assertIn(contract['contract'], ['CALL', 'PUT'])

                    self.assertEqual(type(contract['special']), str)
                    self.assertIn(contract['special'], ['Weeklys', 'Standard', 'Mini'])

                    self.assertEqual(type(contract['strike']), float)
                    self.assertGreater(contract['strike'], 0)

                    self.assertEqual(type(contract['option_code']), str)

                    #print 'current option:'
                    #pprint(option, width=400)

                    for key in option.keys():
                        self.assertIn(key, option_keys)
                        if key == 'date':
                            self.assertEqual(type(option['date']), str)
                            self.assertTrue(datetime.strptime(option['date'], '%Y-%m-%d'))
                        elif key == 'dte':
                            self.assertEqual(type(option['dte']), int)
                        else:
                            self.assertEqual(type(option[key]), float)

                    # try save contract and option
                    c = OptionContract()
                    c.symbol = self.symbol
                    c.load_dict(contract)
                    c.save()
                    self.assertTrue(c.id)

                    o = Option()
                    o.option_contract = c
                    o.load_dict(option)
                    o.save()
                    self.assertTrue(o.id)

                    df_contract = df_contract.append(c.to_hdf())
                    df_options = df_options.append(o.to_hdf())

                    #print '.' * 80
                    #print '\n' + '*' * 100 + '\n'

        print df_contract

        print df_options.to_string(line_width=300)