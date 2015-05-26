from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.models import *


class TestData(TestSetUp):
    def test_underlying(self):
        pass

    def test_stock(self):
        pass

    def test_option_code(self):
        pass


class TestDataImport(TestSetUp):
    def test_web_import_view(self):
        """
        Test web import using google or yahoo into csv
        """
        self.skipTest("Only test when needed...")

        User.objects.create_superuser('root', 'a@a.a', '123456')
        self.client.login(username='root', password='123456')

        source = 'google'
        symbol = 'IWM'

        underlying = Underlying(symbol=symbol)
        underlying.start = '2015-05-20'
        underlying.save()

        print 'run web import view...'
        response = self.client.get(reverse('admin:web_import', args=(source, symbol, )))

        print 'inserted stocks:'
        for stock in response.context['stocks']:
            print stock

        self.assertEqual(
            response.context['title'], '{source} Web Import: {symbol}'.format(
                source=source.capitalize(), symbol=symbol.upper())
        )
        self.assertLessEqual(len(response.context['stocks']), 11)

        stocks = Stock.objects.all()
        self.assertTrue(stocks.exists())

    def test_csv_import_view(self):
        """
        Test csv import file into db
        """
        self.skipTest("Only test when needed...")

        User.objects.create_superuser('root', 'a@a.a', '123456')
        self.client.login(username='root', password='123456')

        symbol = 'AIG'

        underlying = Underlying(symbol=symbol)
        underlying.start = '2015-04-01'
        underlying.save()

        print 'run csv import view...'
        response = self.client.get(reverse('admin:csv_import', args=(symbol, )))

        self.assertGreaterEqual(len(response.context['files']), 1)

        print 'stock count:', Stock.objects.count()
        print 'contract count:', OptionContract.objects.count()
        print 'option count', Option.objects.count()

        self.assertTrue(Stock.objects.count())
        self.assertTrue(OptionContract.objects.count())
        self.assertTrue(Option.objects.count())

        stocks = Stock.objects.all()
        # self.assertGreater(stocks.count(), 0)
        print 'stock count: %d' % Stock.objects.count()
        for stock in stocks[:5]:
            print stock
        else:
            print '...'
            print '.' * 60

        option_contracts = OptionContract.objects.all()
        # self.assertGreater(option_contracts.count(), 0)
        print 'option_contract count: %d' % option_contracts.count()

        for option_contract in option_contracts[:3]:
            print option_contract
        else:
            print '...'
            print '.' * 60

        options = Option.objects.all()
        #self.assertGreater(options.count(), 0)
        print 'options count: %d' % options.count()

        for option in options[:5]:
            print option
        else:
            print '...'
            print '.' * 60

    def test_csv_daily_import(self):
        """
        Test csv import file into db
        """
        User.objects.create_superuser('root', 'a@a.a', '123456')
        self.client.login(username='root', password='123456')

        print 'run csv daily import view...'
        response = self.client.get(reverse('admin:csv_daily_import'))

        symbols = [s[0] for s in Stock.objects.all().values_list('symbol').distinct()]

        for symbol in symbols:
            print '.' * 100 + '\n' + symbol + '\n' + '.' * 100
            stock = Stock.objects.filter(symbol=symbol)

            df = DataFrame()
            for s in stock:
                df = df.append(s.to_hdf())

            print df
            self.assertEqual(stock.count(), 3)
            print '.' * 100 + '\n'


















