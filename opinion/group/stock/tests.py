from django.core.urlresolvers import reverse

from base.utests import TestUnitSetUp
from opinion.group.report.models import UnderlyingReport
from opinion.group.stock.report import ReportStockProfile, ReportUnderlyingArticle
import pandas as pd


class TestStockOpinion(TestUnitSetUp):
    def test_earning_report(self):
        # self.client.get(reverse('report_earning', kwargs={'symbol': 'LUV'}))
        self.client.get(reverse('report_earning', kwargs={'symbol': 'AIG'}))


class TestStockReport(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbol = 'LUV'
        self.date = '2017-02-24'

        self.report_opinion = UnderlyingReport.objects.get(
            symbol=self.symbol, date=self.date
        )

        self.stock_report = ReportStockProfile(self.report_opinion)

    def test_fundamental_report(self):
        """
        Test generate stock fundamental report
        """
        stock_fd_report = self.stock_report.fundamental
        result = stock_fd_report.create()
        print pd.Series(result['rank'])
        print '-' * 70
        print pd.Series(result['date'])
        print '-' * 70
        print pd.Series(result['price'])
        print '-' * 70

        signal, explain = self.stock_report.fundamental.explain_rank()
        print signal
        print explain

        signal, explain = self.stock_report.fundamental.explain_risk()
        print signal
        print explain

        signal, explain = self.stock_report.fundamental.explain_accuracy()
        print signal
        print explain

    def test_industry_report(self):
        """
        Test generate stock industry report
        """
        stock_fd_report = self.stock_report.industry
        result = stock_fd_report.create()
        print pd.Series(result['rank'])
        print '-' * 70
        print pd.Series(result['peer'])
        print '-' * 70

        signal, explain = self.stock_report.industry.explain_rank()
        print signal
        print explain

        signal, explain = self.stock_report.industry.explain_stock()
        print signal
        print explain

    def test_ownership_report(self):
        """
        Test generate stock fundamental report
        """
        result = self.stock_report.ownership.create()
        print pd.Series(result['value'])
        print '-' * 70
        print pd.Series(result['position'])
        print '-' * 70
        #print pd.Series(result['price'])
        #print '-' * 70

        long_safety, explain_hold = self.stock_report.ownership.explain_hold()
        print long_safety
        print explain_hold

        signal, explain_pos = self.stock_report.ownership.explain_pos()
        print signal
        print explain_pos

    def test_insider_report(self):
        """
        Test generate stock insider report
        """
        result = self.stock_report.insider.create()
        print pd.Series(result['share'])
        print '-' * 70

        signal, explain_share = self.stock_report.insider.explain_share()
        print signal
        print explain_share

        signal, explain_price = self.stock_report.insider.explain_price()
        print signal
        print explain_price

    def test_short_interest_report(self):
        """
        Test generate stock insider report
        """
        result = self.stock_report.short_interest.create()
        print pd.Series(result['share'])
        print '-' * 70

        signal, explain_float = self.stock_report.short_interest.explain_float()
        print signal
        print explain_float

        signal, explain_cover = self.stock_report.short_interest.explain_cover()
        print signal
        print explain_cover

    def test_earning_report(self):
        """
        Test generate stock insider report
        """
        result = self.stock_report.earning.create()
        print pd.Series(result['earning'])
        print '-' * 70

        signal, explain_backtest = self.stock_report.earning.explain_backtest()
        print signal
        print explain_backtest


class TestUnderlyingArticleReport(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbol = 'LUV'
        self.date = '2017-02-24'

        self.report_opinion = UnderlyingReport.objects.get(
            symbol=self.symbol, date=self.date
        )

    def test_underlying_article_report(self):
        """

        :return:
        """
        article = ReportUnderlyingArticle(self.report_opinion)
        result = article.create()

        print result['article']
        print '-' * 70
        print result['news']
        print '-' * 70
        print result['behavior']
        print '-' * 70
        print result['article']
        print '-' * 70


