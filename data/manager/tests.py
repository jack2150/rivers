from django.db.models import Q
from base.tests import TestSetUp
from data.manager.manager import StockManager
from data.models import *
from statement.models import Statement


class TestStockManager(TestSetUp):
    fixtures = ('aig_data.json', )
    multi_db = True

    def test_get(self):
        """
        Test manager get stock that ready for testing
        """
        stocks = Stock.objects.filter(Q(symbol='AIG') & Q(source='yahoo'))
        earnings = Earning.objects.filter(symbol='AIG')
        print 'stock count:', stocks.count()
        print 'earnings count:', earnings.count()

        result = StockManager.get(symbol='AIG')

        print 'result count:', result.count()

        self.assertEqual(result.count(), stocks.count() - earnings.count())

        # test include earning date
        print '\n' + '.' * 80 + '\n'
        print 'get stock with earning date...'
        result = StockManager.get(symbol='AIG', earning=True)
        print 'result count:', result.count()
        self.assertEqual(result.count(), stocks.count())
