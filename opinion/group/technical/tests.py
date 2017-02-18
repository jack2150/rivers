from base.utests import TestUnitSetUp
from opinion.group.technical.report import ReportTechnicalRank
from opinion.group.technical.models import TechnicalRank
import pandas as pd


class TestTechnicalReport(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbol = 'CLF'
        self.close = 56.65
        self.date = '2017-01-30'

        self.tech_rank = TechnicalRank.objects.get(
            report__symbol=self.symbol, report__date=self.date
        )
        print self.tech_rank

    def test_marketedge_report(self):
        """
        Test generate marketedge report
        """
        marketedge_report = ReportTechnicalRank.MarketEdge(
            self.tech_rank.technicalmarketedge, self.close
        )
        result = marketedge_report.create()
        print pd.Series(result['date'])
        print '-' * 70
        print pd.Series(result['move'])
        print '-' * 70
        print pd.Series(result['rank'])
        print '-' * 70
        print pd.Series(result['price'])

    def test_barchart_report(self):
        """
        Test generate barchart report
        """
        barchart_report = ReportTechnicalRank.Barchart(
            self.tech_rank.technicalbarchart, self.close
        )
        result = barchart_report.create()
        print pd.Series(result['rank'])
        print '-' * 70
        print pd.Series(result['past'])
        print '-' * 70
        print pd.Series(result['compare'])
        print '-' * 70
        print pd.Series(result['tech'])
        print '-' * 70
        print pd.Series(result['pivot'])

    def test_chartmill_report(self):
        """
        Test generate chartmill report
        """
        chartmill_report = ReportTechnicalRank.Chartmill(
            self.tech_rank.technicalchartmill, self.close
        )
        result = chartmill_report.create()
        print pd.Series(result['rank'])
        print '-' * 70
        print pd.Series(result['trade'])
        print '-' * 70

    def test_to_heatmap(self):
        """
        Test generate Heat map ranking
        """
        marketedge_report = ReportTechnicalRank.MarketEdge(
            self.tech_rank.technicalmarketedge, self.close
        )
        barchart_report = ReportTechnicalRank.Barchart(
            self.tech_rank.technicalbarchart, self.close
        )
        chartmill_report = ReportTechnicalRank.Chartmill(
            self.tech_rank.technicalchartmill, self.close
        )

        print '%s -> %s' % (marketedge_report.market_edge.opinion, marketedge_report.to_heat())
        print '%s -> %s' % (barchart_report.barchart.overall, barchart_report.to_heat())
        print '%s -> %s' % (chartmill_report.chartmill.rank, chartmill_report.to_heat())