from opinion.group.position.models import *


class ReportOpinionPosition(object):
    def __init__(self, report_enter):
        self.report_enter = report_enter
        """:type: ReportEnter """

        self.pos_enter = self.ReportPositionEnter(
            self.report_enter.symbol,
            self.report_enter.positionenter
        )

    class ReportPositionEnter(object):
        def __init__(self, symbol, pos_enter):
            self.symbol = symbol
            self.pos_enter = pos_enter
            """:type: PositionEnter"""

        def create(self):
            """

            :return:
            """
            if self.pos_enter.side == 'long':
                side = 'buy'
                size = self.pos_enter.quantity
            else:
                side = 'sell'
                size = -self.pos_enter.quantity

            ex_date = self.pos_enter.exit_date.strftime('%d %b %y')
            right = 100
            enter_price = float(self.pos_enter.enter_price)

            if self.pos_enter.optionable:
                # BUY +1 BUTTERFLY LUV 100 16 JUN 17 55/60/70 CALL @.75 LMT
                name = '%s %+d %s %s %d %s %s %s @%.2f LMT' % (
                    side,
                    size,
                    self.pos_enter.strategy,
                    self.symbol,
                    right,
                    ex_date,
                    self.pos_enter.strikes,
                    self.pos_enter.option,
                    enter_price
                )
            else:
                # BUY +100 LUV @54.39 LMT
                name = '%s %+d %s @%.2f LMT' % (
                    side,
                    size,
                    self.symbol,
                    enter_price,
                )

            events = {
                'both': 'Earning & Dividend',
                'earning': 'Earning',
                'dividend': 'Dividend',
                'split': 'Split',
                'announcement': 'Announcement',
                'seasonal': 'Seasonal events',
                'multiple': 'Multiple events',
                'none': 'None'
            }

            def get_url(obj):
                if obj:
                    return obj.url
                else:
                    return ''

            return {
                'name': name,
                'move': [
                    ('direction', self.pos_enter.direction),
                    ('target_price', '%.2f' % self.pos_enter.target_price),
                    ('commission', '%.2f' % self.pos_enter.commission),
                ],
                'risk': [
                    ('profile', self.pos_enter.risk_profile.capitalize()),
                    ('margin', '%.0f / %.0f' % (
                        float(self.pos_enter.bp_effect), float(self.pos_enter.capital)
                    )),
                    ('p/l', '+%.2f or -%.2f' % (
                        float(self.pos_enter.max_profit), float(self.pos_enter.max_loss)
                    )),
                ],
                'position': [
                    ('return', '%.2f' % self.pos_enter.expect_return),
                    ('date', '%s to %s' % (
                        self.pos_enter.enter_date, self.pos_enter.exit_date
                    )),
                    ('dte', self.pos_enter.dte),
                ],
                'event': [
                    ('event', self.pos_enter.event_trade),
                    ('cross', events[str(self.pos_enter.event_period)]),
                ],
                'chart': [
                    [
                        ('risk_chart', get_url(self.pos_enter.risk_chart)),
                        ('risk_ex_chart', get_url(self.pos_enter.risk_ex_chart)),
                        ('risk_day_chart', get_url(self.pos_enter.risk_day_chart)),
                    ],
                    [
                        ('risk_uvol_chart', get_url(self.pos_enter.risk_uvol_chart)),
                        ('risk_dvol_chart', get_url(self.pos_enter.risk_dvol_chart)),
                        ('prob_chart', get_url(self.pos_enter.prob_chart)),
                    ],
                    [
                        ('price_chart0', get_url(self.pos_enter.price_chart0)),
                        ('price_chart1', get_url(self.pos_enter.price_chart1)),
                        ('price_chart2', get_url(self.pos_enter.price_chart2)),
                    ],
                    [
                        ('price_chart3', get_url(self.pos_enter.price_chart3)),
                        ('price_chart4', get_url(self.pos_enter.price_chart4)),
                    ],
                ]
            }

        def explain(self):
            """

            :return:
            """
            return '\n'.join(['%s - %s' % (s.capitalize(), e) for s, e in [
                self.explain_margin(),
                self.explain_pl(),
                self.explain_event()
            ]])

        def explain_margin(self):
            """

            :return:
            """
            margin = float(self.pos_enter.bp_effect / self.pos_enter.capital) * 100

            explain = 'You are using %.0f%% of $%.2f total capital.\n' % (
                margin, float(self.pos_enter.capital)
            )

            danger_list = (
                'vertical', 'calendar', 'diagonal', 'condor', 'iron_condor',
            )

            if margin >= 5:
                if self.pos_enter.strategy == 'stock':
                    signal = 'good'
                    explain += 'Stock position, is ok because you cannot loss all.'
                else:
                    signal = 'bad'
                    explain += 'Option position, you are trading too big, close now.'
            elif 2.5 >= margin > 5:
                if self.pos_enter.strategy in danger_list:
                    signal = 'average'
                    explain += '%s position, you are trading too big, close now.' % (
                        self.pos_enter.strategy.capitalize()
                    )
                else:
                    signal = 'good'
                    explain += '%s position, make sure not loss all or in danger zone.' % (
                        self.pos_enter.strategy.capitalize()
                    )
            else:
                signal = 'average'
                explain += '%s position, max loss is low, safe.' % (
                    self.pos_enter.strategy.capitalize()
                )

            return signal, explain

        def explain_pl(self):
            """

            :return:
            """
            trade_off = float(self.pos_enter.max_profit / self.pos_enter.max_loss)

            explain = 'Max profit %.2f is %.2fx to max loss %.2f.\n' % (
                float(self.pos_enter.max_profit), trade_off, float(self.pos_enter.max_loss)
            )

            if trade_off >= 1:
                signal = 'good'
                explain += 'Good trade-off but low probability chance.'
            elif 0.5 >= trade_off > 1:
                signal = 'average'
                explain += 'Average trade, almost 50-50 probability chance.'
            else:
                signal = 'bad'
                explain += 'High probability trade, seek conform but not profit.'

            return signal, explain

        def explain_event(self):
            """

            :return:
            """
            if self.pos_enter.event_trade:
                signal = 'good'
                explain = 'Event trade, make sure careful analysis on earning report.'
            else:
                if self.pos_enter.event_period:
                    signal = 'average'
                    explain = 'Cross %s events within hold period. Be caution.' % (
                        self.pos_enter.event_period.lower()
                    )
                else:
                    signal = 'good'
                    explain = 'No crossing any events within hold period.'

            return signal, explain

