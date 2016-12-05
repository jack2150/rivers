import json
import os
import pandas as pd
from pprint import pprint
from base.utests import TestUnitSetUp
from django.core.urlresolvers import reverse
from subtool.live.excel_rtd.stat import ExcelRtdStatData
from subtool.live.excel_rtd.views import EXCEL_FILE


class TestExcelRTD(TestUnitSetUp):
    def test_excel_rtd_create(self):
        """
        Test add analysis sheet to rtd excel file
        """
        try:
            os.system("TASKKILL /F /IM EXCEL.EXE")
        except Exception:
            pass

        self.client.post(reverse('admin:excel_rtd_create'))
        os.startfile(EXCEL_FILE)


class TestExcelRtdStatData(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbols = ['AIG', 'BP', 'GLD'][2:]

        self.stat = ExcelRtdStatData(self.symbols)
        self.stat.get_data()

    def test_get_data(self):
        """
        Test get data from db
        """
        for df in self.stat.df_all.values():
            print df.tail()
            print 'latest close:', self.stat.latest_close(df)
            self.assertTrue(len(df))
            self.assertEqual(type(df), pd.DataFrame)

    def test_mean_volume(self):
        """
        Test calc mean volume stat
        """
        print 'test calc mean_vol...'
        for symbol in self.symbols:
            df = self.stat.df_all[symbol]

            vol5, vol20 = self.stat.mean_vol(df)
            print 'symbol: %s, days: 5, mean_vol: %d' % (symbol, vol5)
            print 'symbol: %s, days: 20, mean_vol: %d' % (symbol, vol20)

    def test_open_move(self):
        """
        Test calc open to close move stat
        """
        print 'test calc open_move...'
        for symbol in self.symbols:
            df = self.stat.df_all[symbol]
            pprint(self.stat.open_to_close_move(df))

    def test_close_to_open_move(self):
        """
        Test calc open to close move stat
        """
        print 'test calc close_to_open_move...'
        for symbol in self.symbols:
            df = self.stat.df_all[symbol]
            stats = self.stat.close_to_open_move(df)

            for stat in stats:
                print stat.group
                print stat.parts
                print '-' * 70

    def test_high_low(self):
        """
        Test calc high low move width range stat
        """
        print 'test calc high_low...'
        for symbol in self.symbols[:1]:
            df = self.stat.df_all[symbol]
            hl5, hl20 = self.stat.hl_wide(df)
            print 'symbol: %s, days: 5, high_low: %f' % (symbol, hl5)
            print 'symbol: %s, days: 20, high_low: %f' % (symbol, hl20)

    def test_expected_move(self):
        """
        Test previous 60 days close to close move stat
        """
        print 'test calc expected_move...'
        for symbol in self.symbols[:1]:
            df = self.stat.df_all[symbol]
            pprint(self.stat.std_close(df))
