from pprint import pprint

import pandas as pd
from base.utests import TestUnitSetUp
from django.core.urlresolvers import reverse
from opinion.group.market.models import MarketMonthEconomic, MarketWeek
from opinion.group.market.report import ReportMarketMonthEconomic, ReportMarketWeek


class TestReportMarketMonthEconomic(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.month_eco = MarketMonthEconomic.objects.first()

        self.report = ReportMarketMonthEconomic(self.month_eco)

    def test_report(self):
        """
        Test generate stock fundamental report
        """
        report = self.report.create()
        pprint(report)


class TestReportMarketWeek(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.market_week = MarketWeek.objects.first()

        self.report = ReportMarketWeek(self.market_week)

    def test_fund_report(self):
        """
        Test generate stock fundamental report
        """
        report = self.report.fund.create()
        pprint(report)

        # print self.report.fund.explain_fund()
        print self.report.fund.explain_stock()
        print self.report.fund.explain_bond()
        print self.report.fund.explain_money()
        print self.report.fund.explain_credit_balance()

    def test_commitment_report(self):
        """
        Test generate stock fundamental report
        """
        report = self.report.commitment.create()
        pprint(report)









