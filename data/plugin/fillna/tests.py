from django.core.urlresolvers import reverse
from base.tests import TestSetUp
import numpy as np
import pandas as pd
from rivers.settings import QUOTE


class TestOptionCalculator(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbols = [
            'AIG', 'FSLR', 'SNDK', 'DDD', 'BP', 'C', 'CELG',
            'YUM', 'XOM', 'WMT', 'WFC', 'VZ', 'TWTR', 'TSLA', 'PG',
            'DAL', 'DIS', 'EA', 'EBAY', 'FB'
        ]

    def test123(self):
        """
        Test fill missing options
        """
        symbol = self.symbols[0]
        db = pd.HDFStore(QUOTE)
        df_contract0 = db.select('option/%s/clean/contract' % symbol.lower())
        df_option0 = db.select('option/%s/clean/data' % symbol.lower())
        db.close()

        self.client.get(reverse('admin:fillna_option', kwargs={'symbol': symbol.lower()}))

        db = pd.HDFStore(QUOTE)
        df_contract1 = db.select('option/%s/clean/contract' % symbol.lower())
        df_option1 = db.select('option/%s/clean/data' % symbol.lower())
        db.close()

        self.assertGreaterEqual(len(df_option1), len(df_option0))
        self.assertGreaterEqual(
            np.count_nonzero(df_contract1['missing']),
            np.count_nonzero(df_contract0['missing'])
        )

        self.assertEqual(type(df_option1.index), pd.DatetimeIndex)
