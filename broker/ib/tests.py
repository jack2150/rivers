from decimal import Decimal

from django.core.urlresolvers import reverse

from base.dj_tests import TestSetUp
from broker.ib.models import *


class IBStatementTest(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)
        self.fname = 'U1917852_20161111_20161111.csv'
        self.date = datetime.strptime('20161111', '%Y%m%d')

        self.statement_name = IBStatementName()
        self.statement_name.name = 'Interactive brokers'
        self.statement_name.broker_id = 'U1917852'
        self.statement_name.path = 'ib_real_u1917852'
        self.statement_name.start = '2016-11-11'
        self.statement_name.description = 'Testing account'
        self.statement_name.save()

    def test_statement_import(self):
        """
        Test statement import from csv file
        :return:
        """
        statement = IBStatement()
        statement.statement_import(self.statement_name, self.fname)

        ib_statement = IBStatement.objects.first()
        print ib_statement

        ib_nav = IBNetAssetValue.objects.all()
        print 'ib_nav length: %d' % len(ib_nav)
        self.assertTrue(len(ib_nav))

        ib_mark = IBMarkToMarket.objects.all()
        print 'ib_mark length: %d' % len(ib_mark)
        self.assertTrue(len(ib_mark))

        ib_perform = IBPerformance.objects.all()
        print 'ib_perform length: %d' % len(ib_perform)
        self.assertTrue(len(ib_perform))

        print '-' * 70

        keys = ['asset', 'total0', 'total1', 'short_sum', 'long_sum', 'change']
        expects = {
            'Cash': [7886.69, 5711.69, 0, 5711.69, -2175],
            'Stock': [16585.5, 18357, 0, 18357, 1771.5],
            'Total': [24472.19, 24068.69, 0, 24068.69, -403.5]
        }

        for name, expect in expects.items():
            temp = ib_nav.get(asset=name)
            print '%s NAV: %s' % (name.capitalize(), temp)
            self.assertEqual(float(temp.total0), expect[0])
            self.assertEqual(float(temp.total1), expect[1])
            self.assertEqual(float(temp.short_sum), expect[2])
            self.assertEqual(float(temp.long_sum), expect[3])
            self.assertEqual(float(temp.change), expect[4])

            for key in keys:
                print key, getattr(temp, key)

            print '-' * 70

    def test_ib_statement_imports(self):
        """
        Test IB Statement imports all file in folder
        """
        response = self.client.get(reverse('admin:ib_statement_imports', kwargs={
            'ib_path': self.statement_name.path
        }))

        # check redirect
        self.assertRedirects(response, reverse('admin:ib_ibstatement_changelist'))

        ib_statements = IBStatement.objects.all()
        for ib_statement in ib_statements:
            print ib_statement
            self.assertTrue(ib_statement.id)
            nav_sets = ib_statement.ibnetassetvalue_set.all()
            for nav in nav_sets:
                print nav
            self.assertEqual(len(nav_sets), 3)
            self.assertTrue(nav_sets.filter(asset='Cash').exists())
            self.assertTrue(nav_sets.filter(asset='Stock').exists())
            self.assertTrue(nav_sets.filter(asset='Total').exists())

            print '-' * 70









