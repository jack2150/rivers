from base.utests import TestUnitSetUp
from opinion.group.report.models import ReportEnter
from opinion.group.fundamental.report import ReportFundamental
from opinion.group.fundamental.models import StockFundamental, StockIndustry
import pandas as pd


class TestTechnicalReport(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbol = 'CLF'
        self.close = 8.79
        self.date = '2017-01-30'

        self.report_enter = ReportEnter.objects.get(
            symbol=self.symbol, date=self.date
        )

        self.stock_fd = self.report_enter.stockfundamental
        self.stock_id = self.report_enter.stockindustry

        print self.stock_fd

    def test_stockfundamental_report(self):
        """
        Test generate stock fundamental report
        """
        stock_fd_report = ReportFundamental.ReportStockFundamental(self.stock_fd, self.close)
        result = stock_fd_report.create()
        print pd.Series(result['rank'])
        print '-' * 70
        print pd.Series(result['date'])
        print '-' * 70
        print pd.Series(result['price'])
        print '-' * 70

    def test_stockindustry_report(self):
        """
        Test generate stock industry report
        """
        stock_fd_report = ReportFundamental.ReportStockIndustry(self.stock_id, self.close)
        result = stock_fd_report.create()
        print pd.Series(result['rank'])
        print '-' * 70
        print pd.Series(result['peer'])
        print '-' * 70

# todo: here