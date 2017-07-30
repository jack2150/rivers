from pprint import pprint

from django.test import TestCase

# Create your tests here.
from base.utests import TestUnitSetUp
from opinion.group.position.report import ReportOpinionPosition
from opinion.group.report.models import UnderlyingReport


class TestPositionReport(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbol = 'LUV'
        self.date = '2017-02-24'

        self.report_opinion = UnderlyingReport.objects.get(
            symbol=self.symbol, date=self.date
        )

        self.pos_report = ReportOpinionPosition(self.report_opinion)

    def test_pos_enter(self):
        """
        Test generate stock fundamental report
        """
        result = self.pos_report.pos_enter.create()
        pprint(result)

        signal, explain = self.pos_report.pos_enter.explain_margin()
        print signal, ':', explain

        signal, explain = self.pos_report.pos_enter.explain_pl()
        print signal, ':', explain

        signal, explain = self.pos_report.pos_enter.explain_event()
        print signal, ':', explain
