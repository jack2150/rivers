from cdecimal import Decimal
from data.get_data import GetData
from opinion.group.stock.models import *


class ReportStockProfile(object):
    def __init__(self, report):
        self.report = report
        """:type: UnderlyingReport """

        self.fundamental = self.ReportStockFundamental(
            self.report.stockprofile.stockfundamental, self.report.close
        )

        self.industry = self.ReportStockIndustry(
            self.report.stockprofile.stockindustry, self.report.close
        )

        self.outstanding = 0
        self.ownership = None
        if self.report.stockprofile.stockownership.id:
            self.ownership = self.ReportStockOwnership(
                self.report.stockprofile.stockownership, self.report.close
            )
            self.outstanding = self.report.stockprofile.stockownership.outstanding

        self.insider = None
        if self.report.stockprofile.stockinsider.id:
            self.insider = self.ReportStockInsider(
                self.report.stockprofile.stockinsider, self.outstanding, self.report.close
            )

        self.short_interest = None
        if self.report.stockprofile.stockshortinterest.id:
            self.short_interest = self.ReportStockShortInterest(
                self.report.stockprofile.stockshortinterest, self.outstanding, self.report.close
            )

        self.earning = None
        if self.report.stockprofile.stockearning.id:
            self.earning = self.ReportStockEarning(
                self.report.stockprofile.stockearning,
                self.report.close
            )

    class ReportStockFundamental(object):
        def __init__(self, fundamental, close):
            self.fundamental = fundamental
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

            tp_max = float(self.fundamental.tp_max)
            tp_mean = float(self.fundamental.tp_mean)
            tp_min = float(self.fundamental.tp_min)

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

            today = datetime.datetime.today().date()
            period = (today - self.fundamental.report_date).days

            updated = 'Recent rank, usable'
            if period > 60:
                updated = 'Past rank, unusable'

            return {
                'rank': [
                    ('mean_rank', '%d' % self.fundamental.mean_rank),
                    ('accuracy', self.fundamental.accuracy),
                    ('risk', '%s' % self.fundamental.risk.upper()),
                ],
                'date': [
                    ('rank_date', '%s (%d)' % (self.fundamental.report_date, period)),
                    ('latest_rank', self.fundamental.rank_change.upper()),
                    ('updated', updated),
                ],
                'price': [
                    ('tp_max', '$%.2f > $%.2f < $%.2f' % (
                        float(self.fundamental.tp_max),
                        float(self.fundamental.tp_mean),
                        float(self.fundamental.tp_min)
                    )),
                    ('c2max_12m', '%.2f%% > %.2f%% < %.2f%%' % (
                        price_to['max'], price_to['mean'], price_to['min']
                    )),
                    ('c2max_1m', '%.2f%% > %.2f%% < %.2f%%' % (
                        monthly['max'], monthly['mean'], monthly['min']
                    )),
                ]
            }

        def explain(self):
            """

            :return:
            """
            return '\n'.join(['%s - %s' % (s.capitalize(), e) for s, e in [
                self.explain_rank(),
                self.explain_risk(),
                self.explain_accuracy()
            ]])

        def explain_rank(self):
            if 1 <= self.fundamental.mean_rank < 1.8:
                signal = 'strong_buy'
                explain = 'Best fundamental stock that will outlier most other stocks.'
            elif 1.8 <= self.fundamental.mean_rank < 2.6:
                signal = 'buy'
                explain = 'Good fundamental stock that have good status in the market.'
            elif 2.6 <= self.fundamental.mean_rank < 3.4:
                signal = 'hold'
                explain = 'Normal fundamental company stock.'
            elif 3.4 <= self.fundamental.mean_rank < 4.2:
                signal = 'sell'
                explain = 'Bad fundamental stock that have hard time breakout to profit/growth.'
            else:
                signal = 'strong_sell'
                explain = 'Worst fundamental stock that do not do well in long run.'

            return signal, explain

        def explain_risk(self):
            if self.fundamental.risk == 'high':
                if self.fundamental.mean_rank >= 2.6:
                    signal = 'hold'
                elif self.fundamental.mean_rank <= 3.6:
                    signal = 'strong_sell'
                else:
                    signal = 'sell'

                explain = 'Price very volatile that easy drop below 1/2 sd.'
            elif self.fundamental.risk == 'normal':
                if self.fundamental.mean_rank >= 2.6:
                    signal = 'buy'
                elif self.fundamental.mean_rank <= 3.6:
                    signal = 'sell'
                else:
                    signal = 'hold'

                explain = 'Price normally will drop within 1/2 sd.'
            else:
                signal = self.explain_rank()[0]
                explain = 'Price usually stay between 1 sd.'

            return signal, explain

        def explain_accuracy(self):
            temp_rank = self.fundamental.mean_rank

            if 100 >= self.fundamental.accuracy > 80:
                explain = 'Accuracy is very high, analysts usually right. You can trust them.'
            elif 80 >= self.fundamental.accuracy > 60:
                if temp_rank < 3:
                    temp_rank += 0.8
                else:
                    temp_rank -= 0.8

                explain = 'Accuracy is good, but analysts good perform. You can still follow.'
            else:
                if temp_rank < 3:
                    temp_rank += 1.2
                else:
                    temp_rank -= 1.2

                explain = 'Accuracy is bad, thos analysts never correct. Do follow any of them.'

            if 1 <= temp_rank < 1.8:
                signal = 'strong_buy'
            elif 1.8 <= temp_rank < 2.6:
                signal = 'buy'
            elif 2.6 <= temp_rank < 3.4:
                signal = 'hold'
            elif 3.4 <= temp_rank < 4.2:
                signal = 'sell'
            else:
                signal = 'strong_sell'

            return signal, explain

    class ReportStockIndustry(object):
        def __init__(self, industry, close):
            self.industry = industry
            """:type: StockIndustry """
            self.close = close

        def create(self):
            """
            Explain stock industry
            :return: dict
            """
            return {
                'rank': [
                    ('direction', self.industry.direction.upper()),
                    ('isolate', self.industry.isolate),
                    ('industry_rank', self.industry.industry_rank.capitalize()),
                    ('sector_rank', self.industry.sector_rank.capitalize()),
                ],
                'peer': [
                    ('stock_rank', self.industry.stock_rank.upper()),
                    ('stock_growth', self.industry.stock_growth.capitalize()),
                    ('stock_financial', self.industry.stock_financial.capitalize()),
                ]
            }

        def explain(self):
            """

            :return:
            """
            return '\n'.join(['%s - %s' % (s.capitalize(), e) for s, e in [
                self.explain_rank(),
                self.explain_stock()
            ]])

        def explain_rank(self):
            """

            :return:
            """
            explain = '%s industry & %s sector, ' % (
                self.industry.industry_rank, self.industry.sector_rank
            )

            if self.industry.sector_rank == 'top':
                if self.industry.industry_rank == 'top':
                    signal = 'strong_buy'
                    explain += 'top rank good investment.'
                elif self.industry.industry_rank == 'middle':
                    signal = 'buy'
                    explain = 'still can invest some.'
                else:
                    signal = 'sell'
                    explain = 'good sector but bad industry stock.'
            elif self.industry.sector_rank == 'middle':
                if self.industry.industry_rank == 'top':
                    signal = 'buy'
                    explain = 'a good stock.'
                elif self.industry.industry_rank == 'middle':
                    signal = 'hold'
                    explain = 'very average stock.'
                else:
                    signal = 'sell'
                    explain = 'not a good investment.'
            else:
                if self.industry.industry_rank == 'top':
                    signal = 'hold'
                    explain = 'an bad sector outlier industry stock.'
                elif self.industry.industry_rank == 'middle':
                    signal = 'sell'
                    explain = 'a bad stock.'
                else:
                    signal = 'strong_sell'
                    explain = 'a sell candidate stock.'

            return signal, explain

        def explain_stock(self):
            """

            :return:
            """
            if self.industry.stock_rank == 'better':
                signal = 'buy'
                explain = 'A significant edge company that have advantage over peer.'
            elif self.industry.stock_rank == 'same':
                signal = 'hold'
                explain = 'A normal average company in the market.'
            else:
                signal = 'sell'
                explain = 'A bad company compare to industry peer.'

            if self.industry.stock_growth == 'better':
                explain += '\nPossible very good growth stock.'

            if self.industry.stock_financial == 'better':
                explain += '\nPossible very good value stock.'

            return signal, explain

    class ReportStockOwnership(object):
        def __init__(self, ownership, close):
            self.ownership = ownership
            """:type: StockOwnership"""

            self.close = float(close)

            # calc
            # outstanding
            self.share_value = self.close * self.ownership.outstanding
            self.hold_value = float(self.ownership.hold_value)
            self.public_percent = 100 - self.ownership.hold_percent
            self.public_share = self.ownership.outstanding * self.public_percent / 100.0
            self.public_value = self.share_value - self.hold_value
            self.hold_share = self.ownership.hold_percent / 100.0 * self.ownership.outstanding

            # position
            self.pos_net_chg = self.ownership.pos_add - self.ownership.pos_reduce
            self.pos_net_pct = self.pos_net_chg / float(self.ownership.outstanding) * 100

            self.pos_enter_pct = self.ownership.pos_enter / float(self.ownership.outstanding) * 100
            self.pos_exit_pct = self.ownership.pos_exit / float(self.ownership.outstanding) * 100
            self.new_net_chg = self.ownership.pos_enter - self.ownership.pos_exit
            self.new_net_pct = self.new_net_chg / float(self.ownership.outstanding) * 100
            self.pos_ratio = self.ownership.pos_enter / float(self.ownership.pos_exit)

        def create(self):
            """

            :return:
            """
            return {
                'value': [
                    ('outstanding', '%d Mil' % self.ownership.outstanding),
                    ('hold_share', '%d (%d%%)' % (self.hold_share, self.ownership.hold_percent)),
                    ('hold_value', '$%.0f Mil' % self.hold_value),
                    ('public_share', '%d (%d%%)' % (self.public_share, self.public_percent)),
                    ('public_value', '$%.0f Mil' % self.public_value),
                    ('share_value', '$%.0f Mil' % self.share_value),
                ],
                'position': [
                    ('pos_add', '%d' % self.ownership.pos_add),
                    ('pos_reduce', '%d' % self.ownership.pos_reduce),
                    ('pos_net', '%d (%+.2f%%)' % (self.pos_net_chg, self.pos_net_pct)),
                    ('pos_enter', '+%d (+%.2f%%)' % (self.ownership.pos_enter, self.pos_enter_pct)),
                    ('pos_exit', '-%d (-%.2f%%)' % (self.ownership.pos_exit, self.pos_exit_pct)),
                    ('new_net', '%d (%+.2f%%)' % (self.new_net_chg, self.new_net_pct)),
                    ('pos_ratio', '%.2fx' % self.pos_ratio),
                ],
            }

        def explain(self):
            """

            :return:
            """
            return '\n'.join(['%s - %s' % (s.capitalize(), e) for s, e in [
                self.explain_hold(),
                self.explain_pos(),
            ]])

        def explain_hold(self):
            """

            :return:
            """
            holding = [
                'Almost all %d Mils (%d%%) shares or $%.0f Mil is hold by institution. \n'
                'Fund manager are not willing to let public collect the share, \n'
                'maybe you should buy and hold. Is also difficult to short.',
                'There was %d Mils (%d%%) shares or $%.0f Mil is hold by institution. \n'
                'Fund manager are invest large part of this stock, \n'
                'maybe you should buy some.',
                'Only small amount of %d Mils (%d%%) shares or $%.0f Mil is hold by institution. \n'
                'If fund manager don\'t optimism on this stock, \n'
                'maybe you should sell.'
            ]

            if self.ownership.hold_percent > 75:
                explain = holding[0] % (
                    self.hold_share, self.ownership.hold_percent, self.hold_value
                )
                signal = 'buy'
            elif self.ownership.hold_percent > 50:
                explain = holding[1] % (
                    self.hold_share, self.ownership.hold_percent, self.hold_value
                )
                signal = 'hold'
            else:
                explain = holding[2] % (
                    self.hold_share, self.ownership.hold_percent, self.hold_value
                )
                signal = 'sell'

            return signal, explain

        def explain_pos(self):
            """

            :return:
            """
            pos_exists = [
                'Share holder are increased %d (%+.2f%%) shares to their existing position. \n',
                'Share holder are decreased %d (%+.2f%%) shares to their existing position. \n',
            ]

            if self.ownership.pos_add > self.ownership.pos_reduce:
                result0 = pos_exists[0] % (self.pos_net_chg, self.pos_net_pct)
                signal0 = -1
            else:
                result0 = pos_exists[1] % (self.pos_net_chg, self.pos_net_pct)
                signal0 = 1

            pos_roll = [
                'Fund manager are entered total of %d (%+.2f%%) shares.',
                'Fund manager are exited total of %d (%+.2f%%) shares.'
            ]

            if self.ownership.pos_enter > self.ownership.pos_exit:
                result1 = pos_roll[0] % (self.new_net_chg, self.new_net_pct)
                signal1 = -1
            else:
                result1 = pos_roll[1] % (self.new_net_chg, self.new_net_pct)
                signal1 = 1

            signals = [
                'strong_buy', 'buy', 'hold', 'sell', 'strong_sell',
            ]
            signal = signals[2 + signal0 + signal1]

            return signal, result0 + result1

    class ReportStockInsider(object):
        def __init__(self, insider, outstanding, close):
            self.insider = insider
            """:type: StockInsider"""
            self.outstanding = outstanding
            self.close = close

            self.share_bought = self.insider.share_bought / 1000000.0
            self.bought_percent = (
                self.share_bought / float(self.outstanding) * 100
            )
            self.share_sold = self.insider.share_sold / 1000000.0
            self.sold_percent = (
                self.share_sold / float(self.outstanding) * 100
            )
            self.share_change = (self.insider.share_bought - self.insider.share_sold) / 1000000.0
            self.change_percent = (
                self.share_change / float(self.outstanding) * 100
            )

            today = datetime.datetime.today().date()
            self.pass_day = (today - self.insider.report_date).days

            self.price_move = (self.close / self.insider.report_price - 1) * 100

        def create(self):
            """

            :return:
            """
            return {
                'share': [
                    ('bought', '%.2fM (%.2f%%)' % (self.share_bought, self.bought_percent)),
                    ('sold', '%.2fM (%.2f%%)' % (self.sold_percent, self.bought_percent)),
                    ('date', self.insider.report_date),
                    ('pass_day', self.pass_day),
                    ('price_move', '%+.2f%%' % self.price_move)
                ]
            }

        def explain(self):
            """

            :return:
            """
            return '\n'.join(['%s - %s' % (s.capitalize(), e) for s, e in [
                self.explain_share(),
                self.explain_price(),
            ]])

        def explain_share(self):
            """

            :return:
            """
            if self.change_percent > 1:
                explain = 'Insider are buying a lot of share, total %.2fM (%.2f%%). ' % (
                    self.share_bought, self.bought_percent
                )
                explain += 'Maybe they know company are in great shape.'
                signal = 'strong_buy'
            elif 1 >= self.change_percent > 0:
                explain = 'Insider slowly buy share %.2fM (%.2f%%). Normal trade, no bias.' % (
                    self.share_bought, self.bought_percent
                )
                signal = 'buy'
            elif self.change_percent == 0:
                explain = 'No insider trade'
                signal = 'hold'
            elif 0 > self.change_percent >= -1:
                explain = 'Insider slowly buy share %.2fM( %.2f%%). Just normal cash out.' % (
                    self.share_bought, self.bought_percent
                )
                signal = 'sell'
            else:
                explain = 'Insider are selling their share aggressive %.2fM( %.2f%%). ' % (
                    self.share_bought, self.bought_percent
                )
                explain += 'Maybe they know company are in trouble.'
                signal = 'strong_sell'

            return signal, explain

        def explain_price(self):
            """

            :return:
            """

            if self.price_move > 0:
                if self.change_percent > 0:
                    signal = 'strong_buy'
                    explain = 'Insider bought share and price up %.2f%%, maybe some correlation.' % (
                        self.price_move
                    )
                elif self.change_percent < 0:
                    signal = 'hold'
                    explain = 'Insider sold share cash out, ' \
                              'but price still up %.2f%%, no significant correlation.' % (
                                  self.price_move
                              )
                else:
                    signal = 'buy'
                    explain = 'Insider no trading, good fundamental stock so price up %.2f%%.' % (
                        self.price_move
                    )
            else:
                if self.change_percent > 0:
                    signal = 'hold'
                    explain = 'Insider bought share and price down %.2f%%, no correlation.' % (
                        self.price_move
                    )
                elif self.change_percent < 0:
                    signal = 'strong_sell'
                    explain = 'Insider sold and price down %.2f%%, maybe some correlation.' % (
                        self.price_move
                    )
                else:
                    signal = 'sell'
                    explain = 'Insider no trade, bad fundamental stock, so price down %.2f%%.' % (
                        self.price_move
                    )

            return signal, explain

    class ReportStockShortInterest(object):
        def __init__(self, short_interest, outstanding, close):
            self.short_interest = short_interest
            """:type: StockShortInterest"""
            self.outstanding = outstanding
            self.close = close

            self.share_short = self.short_interest.share_short / 1000000.0
            self.short_percent = self.share_short / float(self.outstanding) * 100

            self.price_move = self.close / self.short_interest.report_price - 1

        def create(self):
            """

            :return:
            """
            return {
                'share': [
                    ('share', '%dM (%.2f%%)' % (self.share_short, self.short_percent)),
                    ('move', '%.2f%%' % self.short_interest.share_move),
                    ('day_cover', '%.2f days' % self.short_interest.day_cover),
                    ('float', '%.2f%%' % self.short_interest.share_float),
                ]
            }

        def explain(self):
            """

            :return:
            """
            return '\n'.join(['%s - %s' % (s.capitalize(), e) for s, e in [
                self.explain_float(),
                self.explain_cover(),
                self.explain_move(),
            ]])

        def explain_float(self):
            """

            :return:
            """
            # day cover: number of days required to close out all of the short positions
            # short float:
            if self.short_interest.share_float >= 20:
                signal = 'sell'
                explain = 'Share float high %.2f%%, a lot share to short in market. No investor hold.' % (
                    self.short_interest.share_float
                )
            elif 40 > self.short_interest.share_float >= 10:
                signal = 'hold'
                explain = 'Share float normal %.2f%%, some share remain in market.' % (
                    self.short_interest.share_float
                )
            else:
                signal = 'buy'
                explain = 'Share float low, only %.2f%% basically no share to short. Investor are holding.' % (
                    self.short_interest.share_float
                )

            return signal, explain

        def explain_cover(self):
            """

            :return:
            """
            # day cover: number of days required to close out all of the short positions
            # short float:
            if self.short_interest.day_cover >= 7:
                signal = 'sell'
                explain = 'Short seller have long period %.2f days to cover share.' % (
                    self.short_interest.day_cover
                )
            elif 7 > self.short_interest.day_cover >= 3:
                signal = 'hold'
                explain = 'Short seller have %.2f days to cover share. It is normal.' % (
                    self.short_interest.day_cover
                )
            else:
                signal = 'buy'
                explain = 'Short seller require buy back in %.2f days or will force to recover share.' % (
                    self.short_interest.day_cover
                )

            return signal, explain

        def explain_move(self):
            """

            :return:
            """
            if self.short_interest.share_move >= 20:
                signal = 'sell'
                explain = 'Short sell are more aggressive selling share %+.2f%%' % (
                    self.short_interest.share_move
                )
            elif 20 > self.short_interest.share_move > -20:
                signal = 'hold'
                explain = 'Short sell still increase short position %+.2f%%' % (
                    self.short_interest.share_move
                )
            else:
                signal = 'buy'
                explain = 'Short seller buy back most the share %+.2f%%' % (
                    self.short_interest.share_move
                )

            return signal, explain

    class ReportStockEarning(object):
        def __init__(self, earning, close):
            self.earning = earning
            """:type: StockEarning"""
            self.close = close

        def create(self):
            """

            :return:
            """
            return {
                'earning': [
                    ('direction', '%s %+.1f%%' % (self.earning.direction, self.earning.move)),
                    ('eps', '%s' % self.earning.expect),
                    ('backtest', '%s' % self.earning.backtest),
                ]
            }

        def explain(self):
            """

            :return:
            """
            return '\n'.join(['%s - %s' % (s.capitalize(), e) for s, e in [
                self.explain_backtest(),
                self.explain_esp()
            ]])

        def explain_esp(self):
            """

            :return:
            """
            if self.earning.direction == 'bull':
                signal = 'buy'
            elif self.earning.direction == 'neutral':
                signal = 'hold'
            else:
                signal = 'sell'

            explain = 'Earning estimate eps usually come out "%s".' % (
                self.earning.expect
            )

            return signal, explain

        def explain_backtest(self):
            """

            :return:
            """
            if self.earning.backtest != '':
                if self.earning.backtest == 'bull':
                    signal = 'buy'
                elif self.earning.backtest == 'neutral':
                    signal = 'hold'
                else:
                    signal = 'sell'

                explain = 'Earning backtest come out result is "%s".' % (
                    self.earning.backtest
                )
            else:
                signal = 'neutral'
                explain = 'Currently no earning backtest result.'

            return signal, explain


class ReportUnderlyingArticle(object):
    def __init__(self, report):
        self.report = report
        """:type: UnderlyingReport """

        self.article = self.report.underlyingarticle
        """:type: UnderlyingArticle"""

    def create(self):

        story = {
            'good90': 'Good story 90% chance, 88% follow',
            'good30': 'Good story 30% chance, 78% follow',
            'bad90': 'Bad story 90% chance, 38% follow',
            'bad30': 'Bad story 30% chance, 7% follow'
        }

        follow = 'Not follow'
        if self.article.blind_follow:
            follow = 'Follow'

        return {
            'article': [
                ('name', '%s' % self.article.name.capitalize()),
                ('story', '%s' % story[str(self.article.story)]),
                ('period', '%s' % self.article.period.capitalize()),
            ],
            'news': [
                ('rank', self.article.rank.capitalize()),
                ('effect', self.article.effect.capitalize()),
                ('good/bad', '%d/%d' % (self.article.good_news, self.article.bad_news)),
            ],
            'behavior': [
                ('fundamental', self.article.fundamental_effect),
                ('rational', '%s (%s)' % (self.article.rational, follow)),
                ('reversed', self.article.reversed),
            ],
            'direction': [
                ('bull', '%d%%' % self.article.bull_chance),
                ('neutral', '%d%%' % self.article.range_chance),
                ('bear', '%d%%' % self.article.bear_chance),
            ],
        }

    def explain(self):
        return 0, 0
