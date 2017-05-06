"""
Statement (broker info, added)
Account Information (name, id, so on, added)

Mark-to-Market Performance Summary (done)
Long Open Positions (done)
Short Open Positions (done)
Codes (no need)
Interest Accruals (done)
Net Asset Value (NAV) In Base Currency (done)
Trades (done)
Change in Position Value (done)
Cash Report (done)
Financial Instrument Information (done)
Realized & Unrealized Performance Summary (perform, done)
Month & Year to Date Performance Summary  (pl)

Other Fees (also in cash report)
Broker Interest Paid (also in cash report)
Total P/L for Statement Period (end of month tatal, no need)

Base Currency Exchange Rate (exchange rate)
Notes/Legal Notes (legal)
"""

import re
from decimal import Decimal
from glob import glob

from django.core.urlresolvers import reverse

from base.dj_tests import TestSetUp
from broker.ib.models import *


IB_STATEMENT_NAMES = [
    'stock_prior', 'stock_trans', 'stock_pl_mtm_prior', 'stock_pl_mtm_trans', 'stock_end',
    'option_prior', 'option_trans', 'option_pl_mtm_prior', 'option_pl_mtm_trans', 'option_end',
]

IB_NAV_NAMES = [
    'asset', 'total', 'total_long', 'total_short', 'total_prior', 'total_change'
]

IB_MARK_NAMES = [
    'symbol', 'options', 'qty0', 'qty1', 'price0', 'price1',
    'pl_pos', 'pl_trans', 'pl_fee', 'pl_other', 'pl_total'
]

IB_PERFORM_NAMES = [
    'symbol', 'cost_adj',
    'real_st_profit', 'real_st_loss', 'real_lt_profit', 'real_lt_loss', 'real_total',
    'unreal_st_profit', 'unreal_st_loss', 'unreal_lt_profit', 'unreal_lt_loss', 'unreal_total',
    'total'
]

IB_PL_NAMES = [
    'asset', 'symbol', 'options', 'option_code', 'company', 'pl_mtd', 'pl_ytd',
    'real_st_mtd', 'real_st_ytd', 'real_lt_mtd', 'real_lt_ytd'
]

IB_CR_NAMES = [
    'summary', 'currency', 'total', 'security', 'future', 'pl_mtd', 'pl_ytd'
]

IB_OPEN_NAMES = [
    'statement', 'side', 'asset', 'currency', 'symbol', 'qty', 'multiplier',
    'cost_price', 'cost_basic', 'close_price', 'total_value', 'unreal_pl', 'nav_pct'
]

IB_TRADE_NAMES = [
    'statement', 'asset', 'currency', 'symbol', 'date_time', 'exchange', 'qty',
    'trade_price', 'cost_price', 'proceed', 'fee', 'real_pl', 'real_pl', 'mtm_pl'
]

IB_INFO_NAMES = [
    'statement', 'options', 'asset', 'symbol', 'company', 'con_id',
    'sec_id', 'multiplier'
]

IB_INTEREST_NAMES = [
    'statement', 'currency', 'summary', 'interest',
]

IB_OBJECTS = {
    'ib_nav': (IBNetAssetValue, IB_NAV_NAMES),
    'ib_mark': (IBMarkToMarket, IB_MARK_NAMES),
    'ib_perform': (IBPerformance, IB_PERFORM_NAMES),
    'ib_pl': (IBProfitLoss, IB_PL_NAMES),
    'ib_cash': (IBCashReport, IB_CR_NAMES),
    'ib_open_pos': (IBOpenPosition, IB_OPEN_NAMES),
    'ib_trade': (IBPositionTrade, IB_TRADE_NAMES),
    'ib_info': (IBFinancialInfo, IB_INFO_NAMES),
    'ib_interest': (IBInterestAccrual, IB_INTEREST_NAMES),
}


class IBStatementTest(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)
        self.fname = 'U1917852_20161111_20161111.csv'
        self.year = '2016'
        self.date = datetime.strptime('20161111', '%Y%m%d')

        self.statement_name = IBStatementName()
        self.statement_name.real_name = 'ONG JIN YANG'
        self.statement_name.broker = 'Interactive brokers'
        self.statement_name.account_id = 'U1917852'
        self.statement_name.path = 'ib_real_u1917852'
        self.statement_name.start = '2016-11-30'
        self.statement_name.description = 'Testing account'
        self.statement_name.save()

        self.statement = IBStatement()
        self.statement.statement_name = self.statement_name
        self.statement.date = self.date
        self.statement.save()

    def test_is_statement_name(self):
        """
        :return:
        """
        lines = [
            'Account Information,Data,Name,ONG JIN YANG',
            'Account Information,Data,Account,U1917852',
            'Account Information,Data,Account Capabilities,Margin',
        ]

        info_lines = []
        for line in lines:
            print line,
            result = self.statement_name.is_account(line)
            print result
            self.assertTrue(result)

            if result:
                info_lines.append(line)

        if len(info_lines) == 3:
            result = self.statement_name.match_account(info_lines)
            print 'statement_name match: %s' % result
            self.assertTrue(result)

    def test_is_statement(self):
        """
        :return:
        """
        lines = [
            'Statement,Data,BrokerName,Interactive Brokers',
            'Statement,Data,Title,Activity Statement',
            'Statement,Data,Period,"November 11, 2016"',
        ]

        statement_lines = []
        for line in lines:
            line = re.sub(r'(?!(([^"]*"){2})*[^"]*$),', '', line)  # remove ',' inside quote
            print line
            if self.statement.is_statement(line):
                statement_lines.append(line)

        print 'statement_lines: %d' % len(statement_lines)
        self.assertEqual(len(statement_lines), 3)

        if len(statement_lines) == 3:
            result = self.statement.match_statement(statement_lines)
            print 'statement match: %s' % result

            self.assertTrue(result)

    def test_ib_statement(self):
        """
        Test IBStatement check, extract_csv, save
        """
        lines = [
            'Change in Position Value,Data,STK,USD,Prior Period Value,6816.48',
            'Change in Position Value,Data,STK,USD,Transactions,-1716.35',
            'Change in Position Value,Data,STK,USD,MTM P/L On Prior Period,313.48',
            'Change in Position Value,Data,STK,USD,MTM P/L On Transactions,-3',
            'Change in Position Value,Data,STK,USD,End Of Period Value,5410.61',
            'Change in Position Value,Data,OPT,USD,Prior Period Value,-1172.29',
            'Change in Position Value,Data,OPT,USD,Transactions,1064',
            'Change in Position Value,Data,OPT,USD,MTM P/L On Prior Period,418.68',
            'Change in Position Value,Data,OPT,USD,MTM P/L On Transactions,-58.13',
            'Change in Position Value,Data,OPT,USD,End Of Period Value,252.26',
        ]

        statement = IBStatement()
        statement.statement_name = self.statement_name
        statement.date = self.date
        statement.save()

        for line in lines:
            print statement.is_change_position_value(line),
            print line
            self.assertTrue(statement.is_change_position_value(line))
            statement.extract_csv(line)

        statement.save()
        print statement, statement.id

        print '-' * 70

        for name in IB_STATEMENT_NAMES:
            print '%s = %s' % (name, getattr(statement, name))

    def test_net_asset_value(self):
        """
        Test IBProfitLoss check, extract_csv, save
        """
        lines = [
            'Net Asset Value (NAV) In Base Currency,Data,Cash ,-740.973,0,-740.9731,-640.847260379,-100.12',
            'Net Asset Value (NAV) In Base Currency,Data,Stock,24606,24606,0,24640,-34',
            'Net Asset Value (NAV) In Base Currency,Data,Options,136.99,884.53,-747.54,53.22,83.77',
            'Net Asset Value (NAV) In Base Currency,Data,Total,24002.01,25490.53,-1488.51,24052.37,-50.3559288'
        ]

        for line in lines:
            ib_nav = IBNetAssetValue()

            print ib_nav.is_object(line)
            self.assertTrue(ib_nav.is_object(line))

            ib_nav.extract_csv(self.statement, line)
            ib_nav.save()
            print ib_nav, ib_nav.id
            self.assertTrue(ib_nav.id)

        print '\n' + '=' * 70 + '\n'

        ib_navs = IBNetAssetValue.objects.all()
        print 'ib_navs: %d' % len(ib_navs)

        for ib_nav in ib_navs:
            for name in IB_NAV_NAMES:
                print '%s = %s' % (name, getattr(ib_nav, name))

            print '-' * 70

    def test_mark_to_market(self):
        """
        Test IBMarkToMarket check, extract_csv, save
        """
        lines = [
            'Mark-to-Market Performance Summary,Data,Stocks,UDN,200,200,20.3900,20.4600,14,0,0,0,14,',
            'Mark-to-Market Performance Summary,Data,Stocks,USO,1000,1000,11.7200,11.7200,0,0,0,0,0,',
            'Mark-to-Market Performance Summary,Data,Equity and Index Options,FXI 06JAN17 34.0 C,'
            '-2,-2,0.9687,0.8656,20.62,0,0,0,20.62,',
            'Mark-to-Market Performance Summary,Data,Equity and Index Options,FXI 06JAN17 35.0 C,'
            '2,2,0.3212,0.2538,-13.48,0,0,0,-13.48,',
        ]

        for line in lines:
            ib_mark = IBMarkToMarket()
            print ib_mark.is_object(line)
            self.assertTrue(ib_mark.is_object(line))

            ib_mark.extract_csv(self.statement, line)
            ib_mark.save()
            print ib_mark
            self.assertTrue(ib_mark.id)

            for name in IB_MARK_NAMES:
                print '%s = %s' % (name, getattr(ib_mark, name))

            if ib_mark.options:
                print '-' * 70
                for key in ('options', 'symbol', 'ex_date', 'strike', 'name'):
                    print '%s = %s' % (key, getattr(ib_mark, key))
                print '-' * 70

    def test_performance(self):
        """
        Test IBPerformance check, extract_csv, save
        """
        lines = [
            'Realized & Unrealized Performance Summary,Data,Stocks,UDN,0,0,0,0,0,0,0,-97,0,0,-97,-97,',
            'Realized & Unrealized Performance Summary,Data,Stocks,USO,0,0,0,0,0,0,851.91,0,0,0,851.91,851.91,',
            'Realized & Unrealized Performance Summary,Data,Equity and Index Options,'
            'FXI 06JAN17 34.0 C,0,0,0,0,0,0,0,-78.337492,0,0,-78.337492,-78.337492,',
            'Realized & Unrealized Performance Summary,Data,Equity and Index Options,IWM 30DEC16 136.0 C,'
            '0,0,0,0,0,0,0,-93.0907,0,0,-93.0907,-93.0907,'
        ]

        for line in lines:
            ib_performance = IBPerformance()
            print ib_performance.is_object(line),
            self.assertTrue(ib_performance.is_object(line))

            ib_performance.extract_csv(self.statement, line)
            ib_performance.save()
            print ib_performance
            self.assertTrue(ib_performance.id)

            for name in IB_PERFORM_NAMES:
                print '%s = %s' % (name, getattr(ib_performance, name))

            if ib_performance.options:
                print '-' * 70
                for key in ('options', 'symbol', 'ex_date', 'strike', 'name'):
                    print '%s = %s' % (key, getattr(ib_performance, key))
                print '-' * 70

            print '\n' + '=' * 70 + '\n'

    def test_profit_loss(self):
        """
        Test IBProfitLoss check, extract_csv, save
        """
        lines = [
            'Month & Year to Date Performance Summary,Data,Stocks,VXX,IPATH S&P 500 VIX S/T FU ETN,'
            '-28.958079,-28.958079,-28.958079,-28.958079,0,0',
            'Month & Year to Date Performance Summary,Data,Stocks,XOP,SPDR S&P OIL & GAS EXP & PR,0,'
            '7.904715,0,7.904715,0,0',
            'Month & Year to Date Performance Summary,Data,Equity and Index Options,FXI   170106C00034000,'
            'FXI 06JAN17 34.0 C,-78.337493,-78.337493,0,0,0,0',
            'Month & Year to Date Performance Summary,Data,Equity and Index Options,FXI   170106C00035000,'
            'FXI 06JAN17 35.0 C,17.5486,17.5486,0,0,0,0',
        ]

        for line in lines:
            ib_pl = IBProfitLoss()
            print ib_pl.is_object(line)
            self.assertTrue(ib_pl.is_object(line))

            ib_pl.extract_csv(self.statement, line)
            ib_pl.save()
            print ib_pl
            self.assertTrue(ib_pl.id)

            for name in IB_PL_NAMES:
                print '%s = %s' % (name, getattr(ib_pl, name))

            if ib_pl.options:
                print '-' * 70
                for key in ('options', 'symbol', 'ex_date', 'strike', 'name'):
                    print '%s = %s' % (key, getattr(ib_pl, key))
                print '-' * 70

            print '\n' + '=' * 70 + '\n'

    def test_cash_report(self):
        """
        Test IBCashReport check, extract_csv, save
        """
        lines = [
            'Cash Report,Data,Starting Cash,Base Currency Summary,-640.847260379,'
            '-640.847260379,0,,,',
            'Cash Report,Data,Commissions,Base Currency Summary,-3.125929,-3.125929,0,'
            '-34.094803,-63.58869,',
            'Cash Report,Data,Deposits,Base Currency Summary,0,0,0,0,24980,',
            'Cash Report,Data,Dividends,Base Currency Summary,0,0,0,39.74,39.74,',
            'Cash Report,Data,Ending Settled Cash,Base Currency Summary,22595.94,22595.94,0,',
            'Cash Report,Data,Starting Cash,Base Currency Summary,23772.694,23772.694,0,'
        ]

        for line in lines:
            ib_cash = IBCashReport()

            print ib_cash.is_object(line),
            self.assertTrue(ib_cash.is_object(line))

            ib_cash.extract_csv(self.statement, line)
            ib_cash.save()
            print ib_cash
            self.assertTrue(ib_cash.id)

            for name in IB_CR_NAMES:
                print '%s = %s' % (name, getattr(ib_cash, name))

            print '-' * 70

    def test_open_position(self):
        """
        Test IBOpenPosition check, extract_csv, save
        """
        lines = [
            'Long Open Positions,Data,Summary,Stocks,USD,UNG,-,500,1,8.47396,4236.98,7.17,3585,-651.98,11.95,',
            'Long Open Positions,Data,Summary,Equity and Index Options,USD,C 17MAR17 57.5 C,-,3,100,2.400497667,'
            '720.1493,3.3488,1004.64,284.4907,15.20,',
            'Short Open Positions,Data,Summary,Equity and Index Options,USD,XLF 17MAR17 21.0 P,-,-5,100,0.213548202,'
            '-106.774101,0.2437,-121.85,-15.075899,16.30,'
        ]

        for line in lines:
            ib_open_pos = IBOpenPosition()

            print line, ib_open_pos.is_object(line)
            self.assertTrue(ib_open_pos.is_object(line))

            ib_open_pos.extract_csv(self.statement, line)
            ib_open_pos.save()
            print ib_open_pos, 'id: %d' % ib_open_pos.id
            self.assertTrue(ib_open_pos.id)

            for name in IB_OPEN_NAMES:
                print '%s = %s' % (name, getattr(ib_open_pos, name))

            if ib_open_pos.options:
                print '-' * 70
                for key in ('options', 'symbol', 'ex_date', 'strike', 'name'):
                    print '%s = %s' % (key, getattr(ib_open_pos, key))
                print '-' * 70

            print '\n' + '-' * 70 + '\n'

    def test_position_trade(self):
        """
        Test IBPositionTrade check, extract_csv, save
        """
        # IBPositionTrade
        lines = [
            'Trades,Data,Order,Equity and Index Options,USD,IWM 20JAN17 135.0 C,"2016-12-30, '
            '12:39:09",-,1,2.13,2.12,-213,-1.56,214.5607,0,-1,O',
            'Trades,Data,Trade,Equity and Index Options,USD,IWM 20JAN17 135.0 C,"2016-12-30, '
            '12:39:09",CBOE2,1,2.13,2.12,-213,-1.56,214.5607,0,-1,O',
            'Trades,Data,Order,Equity and Index Options,USD,IWM 20JAN17 137.0 C,"2016-12-30, '
            '12:39:09",-,-1,1.16,1.16,116,-1.56,-114.4347712,0,0,O',
            'Trades,Data,Trade,Equity and Index Options,USD,IWM 20JAN17 137.0 C,"2016-12-30, '
            '12:39:09",CBOE2,-1,1.16,1.16,116,-1.56,-114.4347712,0,0,O',
        ]

        for line in lines:
            ib_pos_trade = IBPositionTrade()

            print line, ib_pos_trade.is_object(line)
            self.assertTrue(ib_pos_trade.is_object(line))

            ib_pos_trade.extract_csv(self.statement, line)
            ib_pos_trade.save()
            print ib_pos_trade, 'id: %d' % ib_pos_trade.id
            self.assertTrue(ib_pos_trade.id)

            for name in IB_TRADE_NAMES:
                print '%s = %s' % (name, getattr(ib_pos_trade, name))

            if ib_pos_trade.options:
                print '-' * 70
                for key in ('options', 'symbol', 'ex_date', 'strike', 'name'):
                    print '%s = %s' % (key, getattr(ib_pos_trade, key))
                print '-' * 70

            print '\n' + '-' * 70 + '\n'

    def test_financial_info(self):
        """
        Test check, extract_csv, save
        """
        lines = [
            'Financial Instrument Information,Data,Stocks,UDN,POWERSHARES DB US DOL IND BE,42930040,,1,',
            'Financial Instrument Information,Data,Stocks,USO,UNITED STATES OIL FUND LP,38590758,,1,',
            'Financial Instrument Information,Data,Equity and Index Options,FXI   170106C00034000,'
            'FXI 06JAN17 34.0 C,256896269,100,2017-01-06,2017-01,C,34,',
            'Financial Instrument Information,Data,Equity and Index Options,FXI   170106C00035000,'
            'FXI 06JAN17 35.0 C,256896278,100,2017-01-06,2017-01,C,35,',
        ]

        for line in lines:
            ib_info = IBFinancialInfo()

            print line, ib_info.is_object(line)
            self.assertTrue(ib_info.is_object(line))

            ib_info.extract_csv(self.statement, line)
            ib_info.save()
            print ib_info, 'id: %d' % ib_info.id
            self.assertTrue(ib_info.id)

            for name in IB_INFO_NAMES:
                print '%s = %s' % (name, getattr(ib_info, name))

            if ib_info.options:
                print '-' * 70
                for key in ('options', 'symbol', 'ex_date', 'ex_month', 'strike', 'name'):
                    print '%s = %s' % (key, getattr(ib_info, key))
                print '-' * 70

            print '\n' + '-' * 70 + '\n'

    def test_interest(self):
        """
        Test check, extract_csv, save
        """
        lines = [
            'Interest Accruals,Data,Base Currency Summary,Starting Accrual Balance,0',
            'Interest Accruals,Data,Base Currency Summary,Interest Accrued,-1.29',
            'Interest Accruals,Data,Base Currency Summary,Accrual Reversal,0',
            'Interest Accruals,Data,Base Currency Summary,Ending Accrual Balance,-1.29',
        ]

        for line in lines:
            ib_interest = IBInterestAccrual()

            print line, ib_interest.is_object(line)
            self.assertTrue(ib_interest.is_object(line))

            ib_interest.extract_csv(self.statement, line)
            ib_interest.save()
            print ib_interest, 'id: %d' % ib_interest.id
            self.assertTrue(ib_interest.id)

            for name in IB_INTEREST_NAMES:
                print '%s = %s' % (name, getattr(ib_interest, name))

            print '\n' + '-' * 70 + '\n'

    def test_statement_import(self):
        """
        Test statement import from csv file
        """
        self.statement.delete()
        ib_statement = IBStatement()
        ib_statement.statement_import(self.statement_name, self.year, self.fname)

        print ib_statement
        print '-' * 70

        for key in IB_STATEMENT_NAMES:
            print key, getattr(ib_statement, key)

        print '\n' + '=' * 70 + '\n'

        # noinspection PyShadowingBuiltins
        for _, (object, names) in IB_OBJECTS.items():
            ib_obj = object
            objects = ib_obj.objects.all()
            print '%s: %d' % (object.__name__.__str__(), len(objects))

            print '-' * 70

            for obj in objects:
                print obj
                for name in names:
                    print '%s: %s' % (name, getattr(obj, name))

                print '\n'

            print '-' * 70 + '\n'

        print '\n' + '=' * 70 + '\n'

    def test_statement_import_loop(self):
        """
        Test statement import for all csv files
        """
        self.statement.delete()

        folder_path = os.path.join(IB_STATEMENT_DIR, self.statement_name.path)
        year_folders = glob(os.path.join(folder_path, '*'))
        for year_folder in year_folders:
            if '__' in year_folder:
                continue

            print 'folder', year_folder

            # data = []
            year_files = glob(os.path.join(year_folder, '*.csv'))
            for fname in year_files:
                print fname

                ib_statement = IBStatement()
                ib_statement.statement_import(self.statement_name, self.year, fname)

                # noinspection PyShadowingBuiltins
                for _, (object, names) in IB_OBJECTS.items():
                    ib_obj_name = '%s_set' % object.__name__.__str__().lower()
                    objects = getattr(ib_statement, ib_obj_name).all()
                    print '%s: %d' % (object.__name__.__str__(), len(objects))

                    print '-' * 70

                    for obj in objects:
                        print obj
                        for name in names:
                            print '%s: %s' % (name, getattr(obj, name)),

                        print '\n'

                print '-' * 70 + '\n'

                print '\n' + '=' * 70 + '\n'

            print 'Object summary'
            # noinspection PyShadowingBuiltins
            for _, (object, names) in IB_OBJECTS.items():
                ib_obj = object
                results = ib_obj.objects.all()
                print '%s: %d' % (object.__name__.__str__(), len(results))

    def test_ib_statement_import_view(self):
        """
        Test IB Statement imports all file in folder
        """
        response = self.client.get(reverse('ib_statement_import', kwargs={
            'obj_id': self.statement.id
        }))

        # noinspection PyShadowingBuiltins
        for _, (object, names) in IB_OBJECTS.items():
            ib_obj = object
            objects = ib_obj.objects.all()
            print '%s: %d' % (object.__name__.__str__(), len(objects))

            print '-' * 70

            for obj in objects:
                print obj
                for name in names:
                    print '%s: %s' % (name, getattr(obj, name))

                print '\n'

            print '-' * 70 + '\n'

        print '\n' + '=' * 70 + '\n'

    def test_ib_statement_imports(self):
        """
        Test IB Statement imports all file in folder
        """
        response = self.client.get(reverse('ib_statement_imports', kwargs={
            'ib_path': self.statement_name.path
        }))

        # check redirect
        # self.assertRedirects(response, reverse('admin:ib_ibstatement_changelist'))

        ib_statements = IBStatement.objects.all()

        for ib_statement in ib_statements:
            print ib_statement
            self.assertTrue(ib_statement.id)

            for key in IB_STATEMENT_NAMES:
                print key, getattr(ib_statement, key)

            print '\n' + '-' * 70 + '\n'

            for (value, names) in IB_OBJECTS.values():
                name = '%s_set' % value.__name__.__str__().lower()
                objects = getattr(ib_statement, name).all()

                print '%s: %d' % (name, len(objects))

                """
                print '-' * 70
                for obj in objects:
                    print obj
                    for name in names:
                        print '%s: %s' % (name, getattr(obj, name)),

                    print '\n'
                """

            print '\n' + '=' * 70 + '\n'
