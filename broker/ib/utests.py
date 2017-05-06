import os

from django.core.urlresolvers import reverse

from base.utests import TestUnitSetUp
from broker.ib.models import *
from broker.ib.views import *
from rivers.settings import CSV_DIR


class TestIBStatementNameCreateCSV(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.ib_statement_name = IBStatementName.objects.get(title='U1917852 Real money')
        self.ib_statements = self.ib_statement_name.ibstatement_set.filter(
            date__range=[self.ib_statement_name.start, self.ib_statement_name.stop]
        ).order_by('date')

    def test_views(self):
        """
        Test Create IBStatement csv files
        """
        self.client.get(
            reverse('ib_statement_create_csv', kwargs={'obj_id': self.ib_statement_name.id})
        )

    def test_nav_to_csv(self):
        """
        Test NetAssetValue to csv file
        """
        nav_to_csv(self.ib_statements)

        fpath = os.path.join(CSV_DIR, IB_STATEMENT_NAME_CSV, IB_EXPORT_NAMES['nav'])
        lines = open(fpath).readlines()

        for line in lines[:20]:
            print line,

    def test_trade_to_csv(self):
        """
        Test PositionTrade to csv file
        """
        trade_to_csv(self.ib_statements)

        fpath = os.path.join(CSV_DIR, IB_STATEMENT_NAME_CSV, IB_EXPORT_NAMES['trade'])
        lines = open(fpath).readlines()

        for line in lines[:60]:
            print line,

    def test_mark_to_csv(self):
        """
        Test MarkToMarket to csv file
        """
        mark_to_csv(self.ib_statements)

        fpath = os.path.join(CSV_DIR, IB_STATEMENT_NAME_CSV, IB_EXPORT_NAMES['mark'])
        lines = open(fpath).readlines()

        for line in lines[:20]:
            print line,


class TestIBStatement(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.ib_statement_name = IBStatementName.objects.get(title='U1917852 Real money')
        self.ib_statement = self.ib_statement_name.ibstatement_set.order_by('date').last()

    def test_create_csv(self):
        """

        :return:
        """
        self.client.get(
            reverse('ib_statement_csv_symbol', kwargs={'obj_id': self.ib_statement.id})
        )

        for key in ('stock', 'option'):
            fname = 'mark_%s_%s.csv' % (
                key, self.ib_statement.date.strftime('%Y%m%d')
            )
            print fname
            fpath = os.path.join(CSV_DIR, IB_STATEMENT_CSV, fname)
            lines = open(fpath).readlines()

            for line in lines[:20]:
                print line,

            print '\n' + '-' * 70 + '\n'


# noinspection PyAttributeOutsideInit
class TestIBPositionCreate(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.ib_statement_name = IBStatementName.objects.get(title='U1917852 Real money')
        self.pos_create = IBPositionCreate(self.ib_statement_name.id)

    def tearDown(self):
        # for testing
        IBPositionTrade.objects.all().update(position=None)
        IBOpenPosition.objects.all().update(position=None)
        IBMarkToMarket.objects.all().update(position=None)
        IBPerformance.objects.all().update(position=None)
        IBProfitLoss.objects.all().update(position=None)
        IBFinancialInfo.objects.all().update(position=None)

        IBPosition.objects.all().delete()

    def test_create(self):
        """
        Test ib position create
        """
        self.pos_create.create()

    def test_create_position_view(self):
        """
        Test the view
        """
        self.client.get(
            reverse('ib_position_create', kwargs={
                'obj_id': self.ib_statement_name.id
            })
        )


# noinspection PyAttributeOutsideInit
class TestIBStatementPositionCreate(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol0 = 'USO'  # stock
        self.symbol1 = 'CLF'  # options

        self.ib_pos0 = IBPosition.objects.filter(
            Q(symbol=self.symbol0) & Q(status='open')
        ).first()
        self.ib_pos1 = IBPosition.objects.filter(symbol=self.symbol1).first()

    def test_position_report_view_stock(self):
        """
        Test the view
        """
        print 'stock: %s' % self.symbol0

        self.client.get(reverse('ib_position_report', kwargs={'obj_id': self.ib_pos0.id}))

    def test_position_report_view_option(self):
        """
        Test the view
        """
        print 'option: %s' % self.symbol1
        self.client.get(reverse('ib_position_report', kwargs={'obj_id': self.ib_pos1.id}))
