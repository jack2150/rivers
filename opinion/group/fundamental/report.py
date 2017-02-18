# todo: report class for stock fd, id
from datetime import datetime

from opinion.group.fundamental.models import StockFundamental, StockIndustry


class ReportFundamental(object):
    def __init__(self, report):
        self.report = report
        """:type: ReportEnter """

        self.stock_fd = self.ReportStockFundamental(self.report.stockfundamental, self.report.close)
        self.stock_id = self.ReportStockIndustry(self.report.stockindustry, self.report.close)

    class ReportStockFundamental(object):
        def __init__(self, stock_fd, close):
            self.stock_fd = stock_fd
            """:type: StockFundamental """
            self.close = float(close)

        def heatmap(self):
            """

            :return:
            """
            return 0

        def create(self):
            """
            Create
            :return:
            """
            explain_rank = self.explain_rank()
            accuracy = self.explain_accuracy()
            explain_risk = self.explain_risk()

            tp_max = float(self.stock_fd.tp_max)
            tp_mean = float(self.stock_fd.tp_mean)
            tp_min = float(self.stock_fd.tp_min)

            price_to = {
                'max': (tp_max / self.close - 1) * 100.0,
                'mean': (tp_mean / self.close - 1) * 100.0,
                'min': (1 - self.close / tp_min) * 100.0
            }
            monthly = {
                'max': price_to['max'] / 12.0,
                'mean': price_to['mean'] / 12.0,
                'min': price_to['min'] / 12.0
            }

            today = datetime.today().date()
            period = (today - self.stock_fd.change_date).days

            updated = 'Recent rank, usable'
            if period > 60:
                updated = 'Past rank, unusable'

            return {
                'rank': [
                    ('mean_rank', '%d %s' % (self.stock_fd.mean_rank, explain_rank)),
                    ('accuracy', accuracy),
                    ('risk', '%s, %s' % (self.stock_fd.risk.upper(), explain_risk)),
                ],
                'date': [
                    ('rank_date', '%s (%d)' % (self.stock_fd.change_date, period)),
                    ('latest_rank', self.stock_fd.rank_change.upper()),
                    ('updated', updated),
                ],
                'price': [
                    ('tp_max', '$%.2f > $%.2f < $%.2f' % (
                        float(self.stock_fd.tp_max),
                        float(self.stock_fd.tp_mean),
                        float(self.stock_fd.tp_min)
                    )),
                    ('c2max_12m', '%.2f%% > %.2f%% < %.2f%%' % (
                        price_to['max'], price_to['mean'], price_to['min']
                    )),
                    ('c2max_1m', '%.2f%% > %.2f%% < %.2f%%' % (
                        monthly['max'], monthly['mean'], monthly['min']
                    )),
                ]
            }

        def explain_rank(self):
            if 1 <= self.stock_fd.mean_rank < 1.8:
                explain = 'Strong buy'
            elif 1.8 <= self.stock_fd.mean_rank < 2.6:
                explain = 'Weak buy'
            elif 2.6 <= self.stock_fd.mean_rank < 3.4:
                explain = 'Hold'
            elif 3.4 <= self.stock_fd.mean_rank < 4.2:
                explain = 'Weak sell'
            else:
                explain = 'Strong sell'

            return explain

        def explain_risk(self):
            if self.stock_fd.risk == 'high':
                explain = 'Easy below 1 sd price'
            elif self.stock_fd.risk == 'normal':
                explain = 'Drop within 1 sd price'
            else:
                explain = 'Stay between 1 sd price'

            return explain

        def explain_accuracy(self):
            if 100 >= self.stock_fd.accuracy > 80:
                explain = 'Can trust'
            elif 80 >= self.stock_fd.accuracy > 60:
                explain = 'Still ok'
            else:
                explain = 'Never correct'

            return '%s %s%%' % (explain, self.stock_fd.accuracy)


    class ReportStockIndustry(object):
        def __init__(self, stock_id, close):
            self.stock_id = stock_id
            """:type: StockIndustry """
            self.close = close

        def create(self):
            """
            Explain stock industry
            :return: dict
            """
            return {
                'rank': [
                    ('direction', self.stock_id.direction.upper()),
                    ('isolate', self.stock_id.isolate),
                    ('industry_rank', self.stock_id.industry_rank.capitalize()),
                    ('sector_rank', self.stock_id.sector_rank.capitalize()),
                ],
                'peer': [
                    ('stock_rank', self.stock_id.stock_rank.upper()),
                    ('stock_growth', self.stock_id.stock_growth.capitalize()),
                    ('stock_financial', self.stock_id.stock_financial.capitalize()),
                ]
            }
