import glob
import os
import pandas as pd
from django.core.urlresolvers import reverse
from pandas.tseries.offsets import BDay

from base.utests import TestUnitSetUp
from data.models import Underlying
from rivers.settings import THINKBACK_DIR


class TestUpdateUnderlying(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

    def test_import_symbols(self):
        """
        Import all underlying in thinkback folders
        """
        # existing symbols
        symbols = [str(u['symbol']) for u in Underlying.objects.values('symbol')]
        m = int(pd.datetime.today().month) - 1
        stop_date = pd.Timestamp('%s%02d%02d' % (
            pd.datetime.today().year,
            (m - (m % 3) + 1),
            1
        )) - BDay(1)

        # new symbols from folder
        new_symbols = []
        for path in glob.glob(os.path.join(THINKBACK_DIR, '*')):
            symbol = os.path.basename(path).upper()

            if symbol not in symbols and symbol != '__DAILY__':
                print 'add symbol: %s' % symbol
                underlying = Underlying(
                    symbol=symbol,
                    stop_date=stop_date
                )
                new_symbols.append(underlying)

        Underlying.objects.bulk_create(new_symbols)
        print 'done bulk_create...'

    def test_update_symbols(self):
        """
        Update empty company symbols in underlying table
        """
        underlyings = Underlying.objects.all()

        for underlying in underlyings:
            if underlying.company == '':
                print 'empty symbol: %s' % underlying.symbol
                print 'run update_underlying...'
                self.client.get(
                    reverse('admin:update_underlying', kwargs={'symbol': underlying.symbol.lower()})
                )
                print 'run add_split_history...'
                self.client.get(
                    reverse('admin:add_split_history', kwargs={'symbol': underlying.symbol.lower()})
                )
            else:
                print 'skip symbol: %s' % underlying.symbol

    def test_output_watchlist(self):
        """
        Output all symbols for copy-past into watchlist
        """
        underlyings = Underlying.objects.all()

        for underlying in underlyings:
            print '%s,' % underlying.symbol

    def test_web_import(self):
        """
        Import web (google/yahoo) for all symbols that not yet import
        """
        underlyings = Underlying.objects.all()

        for underlying in underlyings:
            print 'run %s web import...' % underlying.symbol

        # todo: after thinkback complete











