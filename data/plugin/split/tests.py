from django.core.urlresolvers import reverse
from base.tests import TestSetUp
import numpy as np
import pandas as pd

from data.models import SplitHistory
from rivers.settings import QUOTE


class TestOptionCalculator(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbols = [
            'AIG', 'FSLR', 'SNDK', 'DDD', 'BP', 'C', 'CELG',
            'YUM', 'XOM', 'WMT', 'WFC', 'VZ', 'TWTR', 'TSLA', 'PG',
            'DAL', 'DIS', 'EA', 'EBAY', 'FB'
        ]

    def test_clean_split_stock(self):
        """
        Test fill missing options
        AIG got 5/100 split
        FSLR got 150 bonus issues
        """
        symbol = self.symbols[0]

        split_history = SplitHistory(
            symbol=symbol.upper(),
            date='2009-07-01',
            fraction='5/100'
        )
        split_history.save()

        self.client.get(reverse('admin:clean_split_option', kwargs={'symbol': symbol.lower()}))

    def test_clean_bonus_issue_stock(self):
        """
        Test fill missing options
        DDD got 150 bonus issues
        """
        symbol = self.symbols[3]

        split_history = SplitHistory(
            symbol=symbol.upper(),
            date='2013-02-25',
            fraction='150'
        )
        split_history.save()

        self.client.get(reverse('admin:clean_split_option', kwargs={'symbol': symbol.lower()}))

    def test_merge_split_data(self):
        """
        Test fill missing options
        DDD got 150 bonus issues
        """
        symbol = self.symbols[3]

        split_history = SplitHistory(
            symbol=symbol.upper(),
            date='2013-02-25',
            fraction='2/3'
        )
        split_history.save()

        self.client.get(reverse('admin:merge_split_data', kwargs={'symbol': symbol.lower()}))