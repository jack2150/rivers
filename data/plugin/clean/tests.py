from django.core.urlresolvers import reverse

from base.tests import TestSetUp
from data.plugin.clean.clean import *
import pandas as pd
from rivers.settings import QUOTE
from QuantLib import *


class TestCsvToH5(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'AIG'

    def test_clean_option(self):
        """
        17m 44s pretty good
        :return:
        """
        # self.client.get(reverse('admin:clean_option', kwargs={'symbol': self.symbol.lower()}))
        self.client.get(reverse('admin:clean_option3', kwargs={'symbol': self.symbol.lower()}))

        """
        db = pd.HDFStore(QUOTE)
        df_option = db.select('option/%s/clean/data' % symbol.lower())
        db.close()

        print df_option.to_string(line_width=1000)
        """

        # todo: wrong prob
        # todo: after clean, got wrong rows




