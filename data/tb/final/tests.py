import os

import pandas as pd
from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from base.ufunc import ts
from data.models import Underlying
from data.tb.final.views import update_old_strike, reshape_h5
from rivers.settings import QUOTE_DIR, CLEAN_DIR, BASE_DIR, RESEARCH_DIR


class TestMergeFinal(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'VXX'  # DDD, VXX
        underlying = Underlying(
            symbol=self.symbol,
            start_date='2009-01-01',
            stop_date='2016-01-01'
        )
        underlying.save()

    def test_merge_option_h5(self):
        """
        Test merge fillna option into option and contract db
        """
        self.client.get(reverse('admin:merge_final_h5', kwargs={'symbol': self.symbol.lower()}))

        # get data from db
        path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        df_contract = db.select('option/contract')
        df_option = db.select('option/data')
        db.close()

        print 'df_contract length: %d' % len(df_contract)
        print 'df_option length: %d' % len(df_option)
        self.assertTrue(len(df_contract))
        self.assertTrue(len(df_option))

        ts(df_contract.query('option_code == %r' % 'VXX1121117C92'))
        ts(df_option.query('option_code == %r & date == %r' % ('VXX1121117C92', '2012-09-27')))

        print 'df_contract dtypes:'
        print df_contract.dtypes
        print 'df_option dtypes:'
        print df_option.dtypes

    def test_remove_clean_h5(self):
        """
        Test remove all clean process data
        """
        path = os.path.join(BASE_DIR, 'clean.h5')
        size0 = os.path.getsize(path)
        self.client.get(reverse('admin:remove_clean_h5', kwargs={'symbol': self.symbol.lower()}))

        path = os.path.join(CLEAN_DIR, '__%s__.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        for key in ('raw', 'valid', 'clean', 'fillna'):
            self.assertRaises(lambda: db.select('option/%s/normal' % key))
        db.close()

        # check clean.h5 size
        size1 = os.path.getsize(path)
        print 'clean.h5 file size: %d -> %d' % (size0, size1)
        self.assertGreaterEqual(size0, size1)

    def test_update_strike(self):
        """
        Test update strike for df_split/old
        """
        path = os.path.join(CLEAN_DIR, '__%s__.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        df_split = db.select('option/clean/split/old')
        db.close()

        print 'run update_strike...'
        df_result = update_old_strike(df_split)
        self.assertEqual(len(df_split), len(df_result))

        df_result = df_result.query('option_code == %r' % 'VXX1121117C92')
        print df_result.tail(100).to_string(line_width=1000)

    def test_reshape_h5(self):
        """
        Test reshape h5
        """
        reshape_h5('aig.h5', RESEARCH_DIR)

    def test_open_clean(self):
        """
        Test open clean h5 for view
        :return:
        """
        symbol = 'AIG'
        path = os.path.join(CLEAN_DIR, '__%s__.h5' % symbol.lower())
        db = pd.HDFStore(path)
        df_normal = db.select('option/clean/normal')
        db.close()

        df_date = df_normal[df_normal['date'] == '2011-11-01'].sort_values('dte')
        print df_date.to_string(line_width=1000)

        path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
        db = pd.HDFStore(path)
        df_option = db.select('option/data')
        df_contract = db.select('option/contract')
        df_all = pd.merge(df_option, df_contract, on='option_code')
        db.close()

        df_date = df_all[df_all['date'] == '2011-11-01'].sort_values('dte')
        print df_date.to_string(line_width=1000)




