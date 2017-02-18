from datetime import datetime
from pandas.tseries.offsets import Day, BDay
from models import TechnicalMarketedge, TechnicalBarchart, TechnicalChartmill


class ReportTechnicalRank(object):
    def __init__(self, technical_rank, close):
        self.technical_rank = technical_rank
        """:type: TechnicalRank """
        self.close = float(close)

        self.marketedge = self.MarketEdge(
            self.technical_rank.technicalmarketedge, self.close
        )
        self.barchart = self.Barchart(
            self.technical_rank.technicalbarchart, self.close
        )
        self.chartmill = self.Chartmill(
            self.technical_rank.technicalchartmill, self.close
        )

    class MarketEdge(object):
        def __init__(self, market_edge, close):
            self.market_edge = market_edge
            """:type: TechnicalMarketedge """
            self.close = close

        def to_heat(self):
            """
            opinion value to heat map 0 to 100 only
            """
            return [-1, 90, 70, 50, 30, 10][self.market_edge.opinion]

        def create(self):
            """
            Create marketedge report dict
            """
            # date
            today = datetime.today().date()
            long_ex_date0 = (self.market_edge.date + Day(60)).date()
            long_ex_date1 = (self.market_edge.date + Day(90)).date()
            day_pass = (today - self.market_edge.date).days
            day_pass = day_pass if day_pass else day_pass + 1

            # move
            fprice = float(self.market_edge.fprice)
            period_netchg = round(self.close - fprice, 2)
            period_netpct = round(period_netchg / fprice * 100, 2)

            # rank
            move_valid = self.period_explain(period_netchg)
            power_signal = self.power_explain()
            crate_remain = self.crate_explain()
            score_timing = self.score_explain()

            return {
                'rank': [
                    ('opinion', self.opinion_explain()),
                    ('power', self.market_edge.power),  # same as opinion
                    ('crate', self.market_edge.crate),
                    ('score', self.market_edge.score),
                ],
                'analysis': [
                    ('move_valid', move_valid),
                    ('power_signal', power_signal),
                    ('crate_remain', crate_remain),
                    ('score_timing', score_timing),
                ],
                'price': [
                    ('resist', self.market_edge.resist),
                    ('support', self.market_edge.support),
                    ('stop', self.market_edge.stop),
                    ('position', self.market_edge.position)
                ],
                'move': [
                    ('fprice', fprice),
                    ('period_netchg', period_netchg),
                    ('period_netpct', period_netpct),
                    ('day_avg', period_netpct / day_pass)
                ],
                'date': [
                    ('start', self.market_edge.date),
                    ('stop', '%s to %s' % (long_ex_date0, long_ex_date1)),
                    ('day_pass', day_pass),
                    ('day_remain', '%d to %d' % (
                        (long_ex_date0 - today).days, (long_ex_date1 - today).days
                    ))
                ]
            }

        def opinion_explain(self):
            return [
                '0 None', '1 Long', '2 Neutral from Long', '3 Neutral',
                '4 Neutral from Avoid', '5 Avoid'
            ][self.market_edge.opinion]

        def score_explain(self):
            if self.market_edge.score >= 2:
                score_timing = 'Good condition for profit'
            elif self.market_edge.score >= 0:
                score_timing = 'Normal condition for profit'
            elif self.market_edge.score >= -2:
                score_timing = 'Defensive condition'
            else:
                score_timing = 'Very defensive condition'
            return score_timing

        def period_explain(self, period_netchg):
            if period_netchg > 0:
                if self.market_edge.opinion < 3:
                    valid = True
                else:
                    valid = False
            else:
                if self.market_edge.opinion > 3:
                    valid = False
                else:
                    valid = True
            return valid

        def power_explain(self):
            if self.market_edge.power >= 60:
                power_signal = 'Strong signal & bullish'
            elif self.market_edge.power <= -27:
                power_signal = 'Strong signal & bearish'
            else:
                power_signal = 'Neutral signal'
            return power_signal

        def crate_explain(self):
            if self.market_edge.crate >= 8:
                crate_remain = 'Still can move upside'
            elif self.market_edge.crate <= -4:
                crate_remain = 'Still can move downside'
            else:
                crate_remain = 'Neutral'
            return crate_remain

    class Barchart(object):
        def __init__(self, barchart, close):
            self.barchart = barchart
            """:type: TechnicalBarchart """
            self.close = close

        def to_heat(self):
            """
            opinion value to heat map 0 to 100 only
            """
            return int((self.barchart.overall + 100) / 200.0 * 100)

        def create(self):
            """
            Create barchart report dict
            """
            opinion = self.opinion_explain()
            strength = self.strength_explain()
            direction = self.direction_explain()  # opinion move

            day_to_now = self.barchart.overall - self.barchart.pre_day
            week_to_now = self.barchart.overall - self.barchart.pre_week
            month_to_now = self.barchart.overall - self.barchart.pre_month

            return {
                'rank': [
                    ('overall', '%s %s' % (self.barchart.overall, opinion)),
                    ('strength', '%s %s' % (self.barchart.strength, strength)),
                    ('direction', '%s %s' % (self.barchart.direction, direction)),
                ],
                'past': [
                    ('pre_day', self.barchart.pre_day),
                    ('pre_week', self.barchart.pre_week),
                    ('pre_month', self.barchart.pre_month),
                ],
                'compare': [
                    ('day_to_now', day_to_now),
                    ('week_to_now', week_to_now),
                    ('month_to_now', month_to_now),
                ],
                'tech': [
                    ('day20', self.barchart.day20),
                    ('day50', self.barchart.day50),
                    ('day100', self.barchart.day100),
                ],
                'pivot': [
                    ('resist', self.barchart.resist),
                    ('support', self.barchart.support),
                ]
            }

        def direction_explain(self):
            # 3 days measure
            if self.barchart.direction > 80:
                direction = 'Strongest'
            elif self.barchart.direction > 60:
                direction = 'Strengthening'
            elif self.barchart.direction > 60:
                direction = 'Average'
            elif self.barchart.direction > 60:
                direction = 'Weakening'
            else:
                direction = 'Weakest'

            return direction

        def strength_explain(self):
            if self.barchart.strength > 80:
                strength = 'Maximum'
            elif self.barchart.strength > 60:
                strength = 'Strong'
            elif self.barchart.strength > 40:
                strength = 'Average'
            elif self.barchart.strength > 20:
                strength = 'Weak'
            else:
                strength = 'Minimum'

            return strength

        def opinion_explain(self):
            if self.barchart.overall > 0:
                opinion = 'Buy'
            elif self.barchart.overall < 0:
                opinion = 'Sell'
            else:
                opinion = 'Hold'
            return opinion

    class Chartmill(object):
        def __init__(self, chartmill, close):
            self.chartmill = chartmill
            """:type: TechnicalChartmill """
            self.close = close

        def to_heat(self):
            """
            opinion value to heat map 0 to 100 only
            """
            return int(self.chartmill.rank * 10)

        def create(self):
            """
            Create chartmill report dict
            """
            opinion = self.opinion_explain()
            setup = self.setup_explain()
            p2sr = self.p2sr_explain()

            return {
                'rank': [
                    ('opinion', '%d %s' % (self.chartmill.rank, opinion)),
                    ('setup', '%d %s' % (self.chartmill.setup, setup)),
                    ('p2sr', '%s, %s' % (self.chartmill.p2sr, p2sr)),
                    ('comment', '%d / %d' % (self.chartmill.good, self.chartmill.bad)),
                ],
                'trade': [
                    ('trade', self.chartmill.trade_signal),
                    ('entry', self.chartmill.trade_entry),
                    ('exit', self.chartmill.trade_exit),
                    ('capital', self.chartmill.trade_capital),
                ]
            }

        def p2sr_explain(self):
            if self.chartmill.p2sr == 'high':
                p2sr = 'Price > resist'
            elif self.chartmill.p2sr == 'low':
                p2sr = 'Price < support'
            else:
                p2sr = 'Price in s/r'

            return p2sr

        def setup_explain(self):
            if self.chartmill.setup > 6:
                setup = 'Good enter timing'
            elif self.chartmill.setup > 3:
                setup = 'Normal enter timing'
            else:
                setup = 'Do not enter'

            return setup

        def opinion_explain(self):
            if self.chartmill.rank > 6:
                opinion = 'Buy'
            elif self.chartmill.rank < 4:
                opinion = 'Sell'
            else:
                opinion = 'Hold'

            return opinion
