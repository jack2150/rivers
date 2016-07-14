import os

import pandas as pd
from django.core.urlresolvers import reverse

from base.tests import TestSetUp
from data.event.views import group_event_files
from data.models import Underlying
from rivers.settings import QUOTE_DIR, BASE_DIR


class TestEventImport(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        for symbol in ('GOOG', 'YUM', 'AIG', 'JPM', 'DIS'):
            underlying = Underlying()
            underlying.symbol = symbol
            underlying.start_date = pd.Timestamp('20010101').date()
            underlying.stop_date = pd.Timestamp('20160101').date()
            underlying.save()

    def test_earning_import_form(self):
        """
        Test verify event form and handle file upload then verify earning
        """
        for symbol in ('DIS',):  # ('JPM', 'DDD'):
            print 'running symbol:', symbol
            self.client.get(reverse('admin:html_event_import', kwargs={'symbol': symbol}))

            path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
            db = pd.HDFStore(path)
            df_earning = db.select('event/earning')
            print df_earning.to_string(line_width=600)
            self.assertTrue(len(df_earning))
            db.close()

            db = pd.HDFStore(path)
            df_dividend = db.select('event/dividend')
            print df_dividend.to_string(line_width=600)
            self.assertTrue(len(df_dividend))
            db.close()

    def test_group_event_files(self):
        """
        Test move file from __raw__ into earnings and dividends folder
        """
        group_event_files()

        earning_files = os.path.join(BASE_DIR, 'files', 'fidelity', 'earnings', '*.*')
        dividend_files = os.path.join(BASE_DIR, 'files', 'fidelity', 'dividends', '*.*')

        self.assertGreater(len(earning_files), 1)
        self.assertGreater(len(dividend_files), 1)
