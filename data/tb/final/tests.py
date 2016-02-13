import os

import pandas as pd
from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.models import Underlying
from data.tb.final.views import update_strike
from rivers.settings import QUOTE, CLEAN, BASE_DIR


class TestMergeFinal(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'DDD'
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
        db = pd.HDFStore(CLEAN)
        df_contract = db.select('option/%s/final/contract' % self.symbol.lower())
        df_option = db.select('option/%s/final/option' % self.symbol.lower())
        db.close()

        print 'df_contract length: %d' % len(df_contract)
        print 'df_option length: %d' % len(df_option)
        self.assertTrue(len(df_contract))
        self.assertTrue(len(df_option))

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

        db = pd.HDFStore(CLEAN)
        for key in ('raw', 'valid', 'clean', 'fillna'):
            self.assertRaises(lambda: db.select('option/%s/%s/normal' % (self.symbol.lower(), key)))
        db.close()

        # check clean.h5 size
        size1 = os.path.getsize(path)
        print 'clean.h5 file size: %d -> %d' % (size0, size1)
        self.assertGreaterEqual(size0, size1)

    def test_update_strike(self):
        """
        Test update strike for df_split/old
        """
        db = pd.HDFStore(CLEAN)
        df_split = db.select('option/aig/clean/split/old')
        db.close()

        print 'run update_strike...'
        df_result = update_strike(df_split)
        self.assertEqual(len(df_split), len(df_result))

        print df_result.tail(100).to_string(line_width=1000)
