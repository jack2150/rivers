import glob

import numpy as np
import pandas as pd
from base.utests import TestUnitSetUp
from data.tb.groupOption.groupOption import GroupOption, ComplexGroupOptions, ThinkbackOption
from data.tb.raw.stocks import extract_stock
from django.core.urlresolvers import reverse
from rivers.settings import QUOTE_DIR, DB_DIR, BASE_DIR
from data.tb.raw.options import *

# 'FSLR', 'DDD', 'C', 'TWTR', 'DAL', 'BXP'
symbols = [s.upper() for s in [
    os.path.basename(f) for f in glob.glob(os.path.join(THINKBACK_DIR, '*'))
] if s not in ('__daily__', 'spy', 'uvxy')]


class TestGroupOption(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'UVXY'
        self.path = os.path.join(DB_DIR, 'temp', 'test_%s.h5' % self.symbol.lower())

        path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        self.df_stock = db.select('stock/thinkback')
        print 'df_stock length: %d' % len(self.df_stock)
        db.close()

        self.split_history = SplitHistory.objects.filter(symbol=self.symbol.upper())
        self.group_option = GroupOption(self.symbol, self.df_stock, self.split_history)

    def test_remove_duplicated(self):
        """
        Test remove duplicated rows in df_all
        """
        self.group_option.convert_data()
        self.group_option.remove_duplicate()

    def test_check_code_no_extra(self):
        """
        Test check new code have no extra when there was split/others
        """
        self.group_option.convert_data()
        self.group_option.remove_duplicate()
        self.group_option.prepare_extra()
        self.group_option.update_code()
        self.group_option.check_code_no_extra()

    def test_prepare_extra(self):
        """
        Prepare extra code change
        """
        self.group_option = GroupOption(self.symbol, self.df_stock)
        self.group_option.convert_data()
        self.group_option.remove_duplicate()
        df_date = self.group_option.prepare_extra()

        print df_date

    def test_prepare_extra_mass(self):
        """
        Test prepare extra before update code
        """
        for symbol in symbols:
            self.symbol = symbol

            path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())

            db = pd.HDFStore(path)
            try:
                self.df_stock = db.select('stock/thinkback')
                print 'df_stock: %d' % len(self.df_stock)
            except KeyError:
                extract_stock(self.symbol)
            db.close()

            self.group_option = GroupOption(self.symbol, self.df_stock)
            self.group_option.convert_data()
            self.group_option.remove_duplicate()
            df_date = self.group_option.prepare_extra()

            print df_date

    def test_change_code(self):
        """
        Test major change option_code
        """
        db = pd.HDFStore(self.path)
        try:
            self.group_option.df_all = db['df_all0']
        except KeyError:
            self.group_option.convert_data()
            self.group_option.remove_duplicate()
            db['df_all0'] = self.group_option.df_all
        db.close()

        self.group_option.update_code()

    def test_modify_others(self):
        """
        Test others is actually split data
        """
        db = pd.HDFStore(self.path)
        try:
            self.group_option.df_all = db['df_all1']
        except KeyError:
            self.group_option.convert_data()
            self.group_option.remove_duplicate()
            db['df_all1'] = self.group_option.df_all
        db.close()

        self.group_option.modify_others()

    def test_check_split_others(self):
        """
        Check which class to use to group options
        """
        db = pd.HDFStore(self.path)
        try:
            self.group_option.df_all = db['df_all2']
        except KeyError:
            self.group_option.convert_data()
            self.group_option.remove_duplicate()
            self.group_option.update_code()
            db['df_all2'] = self.group_option.df_all
        db.close()

        proc = self.group_option.check_split_others()

        print 'Using process:', proc

    def test_update_non_standard(self):
        """
        Test update non_standard into existing split/others
        primary for: UVXY
        """
        self.group_option.convert_data()
        self.group_option.update_non_standard()

    def test_all(self):
        """
        Test all methods in group_option
        BAC, BP, GOOG, WFC problem fixed
        """
        self.group_option.convert_data()
        df_date = self.group_option.ready_data(debug=True)

        print df_date

    def test_mass(self):
        """
        Test all symbols in database
        """
        debug = ''
        for symbol in symbols:
            self.symbol = symbol

            path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())

            db = pd.HDFStore(path)
            try:
                self.df_stock = db.select('stock/thinkback')
                print 'df_stock: %d' % len(self.df_stock)
            except KeyError:
                extract_stock(self.symbol)
            db.close()

            self.group_option = GroupOption(self.symbol, self.df_stock)
            self.group_option.convert_data()
            df_date = self.group_option.ready_data(debug=True)
            print df_date

            debug += symbol + '\n'
            debug += df_date.to_string(line_width=200)
            debug += '\n' + '-' * 70 + '\n\n'

            print '\n' + '=' * 70 + '\n'

        f = open(os.path.join(BASE_DIR, 'debug.txt'), mode='w')
        f.write(debug)
        f.close()


class TestComplexGroupOptions(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = ['AIG', 'TZA', 'WFC', 'VZ', 'TNA', 'UVXY', 'FSLR'][2]
        self.split_history = SplitHistory.objects.filter(symbol=self.symbol.upper())

        path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        try:
            self.df_stock = db.select('stock/thinkback')
        except KeyError:
            extract_stock(self.symbol)
        db.close()

        self.path = os.path.join(DB_DIR, 'temp', 'test_%s.h5' % self.symbol.lower())
        db = pd.HDFStore(self.path)
        try:
            # raise KeyError
            self.df_all = db['df_all']
        except KeyError:
            self.group_option = GroupOption(self.symbol, self.df_stock, self.split_history)
            self.group_option.convert_data()
            self.group_option.ready_data()
            db['df_all'] = self.group_option.df_all
            self.df_all = self.group_option.df_all
        db.close()

        self.complex_group = ComplexGroupOptions(self.df_all, self.split_history)
        self.complex_group.prepare_set()

    def test_groupby(self):
        """
        Primary test, AIG, TZA, WFC, VZ, UVXY
        Test groupby split/others into df_date
        """
        self.complex_group.group_data()
        print self.complex_group.df_date

    def test_others_is_split(self):
        """
        Test others is actually split convert, for TZA, UVXY
        """
        self.complex_group.group_data()
        print self.complex_group.df_date
        self.complex_group.others_is_split()
        self.complex_group.group_data()  # regroup data
        print self.complex_group.df_date

    def test_mass(self):
        """
        Test mass groupby for all symbols
        """
        for symbol in symbols:
            self.symbol = symbol

            path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())

            db = pd.HDFStore(path)
            try:
                self.df_stock = db.select('stock/thinkback')
                print 'df_stock: %d' % len(self.df_stock)
            except KeyError:
                extract_stock(self.symbol)
            db.close()

            path2 = os.path.join(DB_DIR, 'temp', 'test_all.h5')
            db = pd.HDFStore(path2)
            try:
                self.df_all = db[symbol]
            except KeyError:
                self.group_option = GroupOption(self.symbol, self.df_stock)
                self.group_option.convert_data()
                self.group_option.remove_duplicate()
                self.group_option.modify_others()
                self.group_option.update_code()
                db[symbol] = self.group_option.df_all
                self.df_all = self.group_option.df_all
            db.close()

            self.complex_group = ComplexGroupOptions(self.df_all, self.split_history)
            self.complex_group.group_data()
            self.complex_group.others_is_split()
            self.complex_group.group_data()
            print self.complex_group.df_date

            print '\n' + '*' * 70 + '\n'

    def test_join_data(self):
        """
        Test join split/others data with continuous normal/split/others data
        """
        db = pd.HDFStore(self.path)
        try:
            # raise KeyError
            self.complex_group.df_normal = db['df_normal']
            self.complex_group.df_remain = db['df_remain']
            self.complex_group.df_date = db['df_date']
        except KeyError:
            self.complex_group.group_data()
            self.complex_group.others_is_split()
            self.complex_group.group_data()

            db['df_normal'] = self.complex_group.df_normal
            db['df_remain'] = self.complex_group.df_remain
            db['df_date'] = self.complex_group.df_date

        db.close()

        # print df_date
        df_list = self.complex_group.join_data()

        for key, df in df_list.items():
            print key, len(df)
            # ts(df.head(10))
            # ts(df.tail(10))
            # c = df.iloc[0]['option_code']
            # ts(df[df['option_code'] == c])

            print '\n' + '-' * 70 + '\n'


class TestThinkbackOption(TestUnitSetUp):
    def setUp(self):
        self.symbol = 'AIG'
        self.tb_option = ThinkbackOption(self.symbol)

    def test_start(self):
        """
        Test create option raw data then save into clean h5 store
        """
        self.tb_option.create_raw()

