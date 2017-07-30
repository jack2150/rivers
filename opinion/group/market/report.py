from opinion.group.market.models import *


class ReportMarketMonthEconomic(object):
    def __init__(self, month_eco):
        self.month_eco = month_eco
        """:type: MarketMonthEconomic"""

    def create(self):
        """

        :return:
        """
        print self.month_eco
        print self.month_eco.eco_cycle
        print self.month_eco.get_eco_cycle_display()




        return {
            'eco': [
                ('cycle', self.month_eco.get_eco_cycle_display()),
                ('index', self.month_eco.get_eco_index_display()),
                ('', '')
            ]
        }

    def explain(self):
        """

        :return:
        """

        return []


class ReportMarketWeek(object):
    def __init__(self, market_week):
        self.market_week = market_week
        """:type: MarketWeek"""

        print self.market_week.marketweekfund

        self.fund = self.ReportMarketWeekFund(
            self.market_week.marketweekfund,
            self.market_week.marketweekfundnetcash_set
        )

        self.commitment = self.ReportMarketWeekCommitment(
            self.market_week.marketweekcommitment_set
        )

    class ReportMarketWeekFund(object):
        def __init__(self, fund, net_cash):
            self.fund = fund
            """:type: MarketWeekFund"""
            self.net_cash = net_cash

            self.stock = self.net_cash.get(name='stock')
            """:type: MarketWeekFundNetCash"""
            self.hybrid = self.net_cash.get(name='hybrid')
            """:type: MarketWeekFundNetCash"""
            self.tax_bond = self.net_cash.get(name='tax_bond')
            """:type: MarketWeekFundNetCash"""
            self.muni_bond = self.net_cash.get(name='muni_bond')
            """:type: MarketWeekFundNetCash"""
            self.money = self.net_cash.get(name='money')
            """:type: MarketWeekFundNetCash"""

            self.stock_chg = float(self.stock.value_chg / (self.stock.total_asset * 1000) * 100)
            self.hybrid_chg = float(self.hybrid.value_chg / (self.hybrid.total_asset * 1000) * 100)
            self.tax_bond_chg = float(self.tax_bond.value_chg / (self.tax_bond.total_asset * 1000) * 100)
            self.muni_bond_chg = float(self.muni_bond.value_chg / (self.muni_bond.total_asset * 1000) * 100)
            self.money_chg = float(self.money.value_chg / (self.money.total_asset * 1000) * 100)

            self.total = (
                self.stock.value_chg + self.stock.value_chg + self.tax_bond.value_chg
                + self.muni_bond.value_chg + self.money.value_chg
            )
            self.total_asset = (
                self.stock.total_asset + self.stock.total_asset + self.tax_bond.total_asset
                + self.muni_bond.total_asset + self.money.total_asset
            )
            self.total_chg = self.total / float(self.total_asset)

        def create(self):
            return {
                'stock': [
                    ('stock', '%d/%.1f (%.1f%%)' % (
                        self.stock.value_chg, self.stock.total_asset, self.stock_chg
                    )),
                    ('hybrid', '%d/%.1f (%.1f%%)' % (
                        self.hybrid.value_chg, self.hybrid.total_asset, self.hybrid_chg
                    )),
                ],
                'bond': [
                    ('tax_bond', '%d/%.1f (%.1f%%)' % (
                        self.tax_bond.value_chg, self.tax_bond.total_asset, self.tax_bond_chg
                    )),
                    ('muni_bond', '%d/%.1f (%.1f%%)' % (
                        self.muni_bond.value_chg, self.muni_bond.total_asset, self.muni_bond_chg
                    )),
                ],
                'flow': [
                    ('money', '%d/%.1f (%.1f%%)' % (
                        self.money.value_chg, self.money.total_asset, self.money_chg
                    )),
                    ('fund_usa', '%d/%.1f (%.1f%%)' % (
                        self.total, self.total_asset, self.total_chg
                    )),
                ]
            }

        def explain(self):
            """

            :return:
            """
            return '\n'.join(['%s - %s' % (s.capitalize(), e) for s, e in [
                self.explain_stock(),
                self.explain_bond(),
                self.explain_money(),
                self.explain_credit_balance(),
            ]])

        def explain_stock(self):
            stock_chg = self.stock_chg + self.hybrid_chg

            if stock_chg > 0.5:
                explain = 'Fund manager are buying stock & hybrid (%.1f%%).\n' % (
                    stock_chg
                )

                if self.fund.margin_debt == 'buy':
                    signal = 'strong_buy'
                    explain += 'They are borrowing heavily to buy.'
                elif self.fund.margin_debt == 'hold':
                    signal = 'buy'
                    explain += 'Normal borrow leverage to buy stock.'
                else:
                    signal = 'hold'
                    explain += 'They mostly use cash to buy.'

            elif stock_chg < -0.5:
                explain = 'Fund manager are selling stock & hybrid (%.1f%%).\n' % (
                    stock_chg
                )

                if self.fund.margin_debt == 'buy':
                    signal = 'hold'
                    explain += 'They are borrowing heavily to buy.'
                elif self.fund.margin_debt == 'hold':
                    signal = 'sell'
                    explain += 'Normal borrow leverage to buy stock.'
                else:
                    signal = 'strong_sell'
                    explain += 'They mostly use cash to sell.'
            else:
                explain = 'Stock & hybrid are in trading range (%.1f%%).\n' % (
                    stock_chg
                )

                if self.fund.margin_debt == 'buy':
                    signal = 'buy'
                    explain += 'They are borrowing heavily to buy.'
                elif self.fund.margin_debt == 'hold':
                    signal = 'hold'
                    explain += 'Normal borrow leverage to buy stock.'
                else:
                    signal = 'sell'
                    explain += 'They mostly use cash to buy.'

            return signal, explain

        def explain_bond(self):
            bond_chg = self.tax_bond_chg + self.muni_bond_chg

            if bond_chg > 0.5:
                # signal = 'buy'
                explain = 'Fund manager are buying taxed-bond & muni-bond (%.1f%%).\n' % (
                    bond_chg
                )

                if self.fund.confidence_index == 'buy':
                    signal = 'hold'
                    explain += 'They buy stock; sell bond. So bond yield higher.'
                elif self.fund.margin_debt == 'hold':
                    signal = 'buy'
                    explain += 'They buy stock; buy bond. So bond yield normal.'
                else:
                    signal = 'strong_buy'
                    explain += 'They sell stock, buy bond. So bond yield lower.'
            elif bond_chg < -0.5:
                # signal = 'sell'
                explain = 'Fund manager are selling taxed-bond & muni-bond (%.1f%%).' % (
                    bond_chg
                )

                if self.fund.confidence_index == 'strong_sell':
                    signal = 'buy'
                    explain += 'They buy stock; sell bond. So bond yield higher.'
                elif self.fund.margin_debt == 'sell':
                    signal = 'hold'
                    explain += 'They buy stock; buy bond. So bond yield normal.'
                else:
                    signal = 'hold'
                    explain += 'They sell stock, buy bond. So bond yield lower.'
            else:
                # signal = 'hold'
                explain = 'Taxed-bond & muni-bond are in trading range (%.1f%%).' % (
                    bond_chg
                )

                if self.fund.confidence_index == 'sell':
                    signal = 'buy'
                    explain += 'They buy stock; sell bond. So bond yield higher.'
                elif self.fund.margin_debt == 'hold':
                    signal = 'hold'
                    explain += 'They buy stock; buy bond. So bond yield normal.'
                else:
                    signal = 'buy'
                    explain += 'They sell stock, buy bond. So bond yield lower.'

            return signal, explain

        def explain_money(self):
            if self.total_chg > 0.5:
                signal = 'buy'
                explain = 'Fund are entering into USA market and waiting to trade (%.1f%%).' % (
                    self.total_chg
                )
            elif self.total_chg < -0.5:
                signal = 'sell'
                explain = 'Fund are exiting from USA market (%.1f%%).' % (
                    self.total_chg
                )
            else:
                signal = 'hold'
                explain = 'Fund are trading in/out range from USA (%.1f%%).' % (
                    self.total_chg
                )

            return signal, explain

        def explain_credit_balance(self):
            if self.fund.credit_balance == 'buy':
                signal = 'buy'
                explain = 'Fund manager are mainly focus invest in stock.'
            else:
                signal = 'sell'
                explain = 'Fund manager are mainly focus invest in bond.'

            return signal, explain

    class ReportMarketWeekCommitment(object):
        def __init__(self, commitment):
            self.commitment = commitment

            self.sp500 = self.commitment.get(name='sp500')
            """:type: MarketWeekCommitment"""
            self.nasdaq = self.commitment.get(name='nasdaq')
            """:type: MarketWeekCommitment"""
            self.djia = self.commitment.get(name='djia')
            """:type: MarketWeekCommitment"""
            self.rs2000 = self.commitment.get(name='rs2000')
            """:type: MarketWeekCommitment"""

            self.oil = self.commitment.get(name='oil')
            """:type: MarketWeekCommitment"""
            self.gas = self.commitment.get(name='gas')
            """:type: MarketWeekCommitment"""
            self.gold = self.commitment.get(name='gold')
            """:type: MarketWeekCommitment"""
            self.bond10y = self.commitment.get(name='bond10y')
            """:type: MarketWeekCommitment"""
            self.bond2y = self.commitment.get(name='bond2y')
            """:type: MarketWeekCommitment"""
            self.dollar = self.commitment.get(name='dollar')
            """:type: MarketWeekCommitment"""

        def create(self):
            sp500_chg = self.sp500.change / float(self.sp500.open_interest) * 100
            nasdaq_chg = self.nasdaq.change / float(self.nasdaq.open_interest) * 100
            djia_chg = self.djia.change / float(self.djia.open_interest) * 100
            rs2000_chg = self.rs2000.change / float(self.rs2000.open_interest) * 100

            oil_chg = self.oil.change / float(self.oil.open_interest) * 100
            gas_chg = self.gas.change / float(self.gas.open_interest) * 100

            gold_chg = self.gold.change / float(self.gold.open_interest) * 100

            bond30y_chg = self.bond10y.change / float(self.bond10y.open_interest) * 100
            bond2y_chg = self.bond2y.change / float(self.bond2y.open_interest) * 100

            dollar_chg = self.dollar.change / float(self.dollar.open_interest) * 100

            return {
                'indices': [
                    ('sp500', '%d/%d (%+.1f%%)' % (
                        self.sp500.change, self.sp500.open_interest, sp500_chg
                    )),
                    ('nasdaq', '%d/%d (%+.1f%%)' % (
                        self.nasdaq.change, self.nasdaq.open_interest, nasdaq_chg
                    )),
                    ('djia', '%d/%d (%+.1f%%)' % (
                        self.djia.change, self.djia.open_interest, djia_chg
                    )),
                    ('rs2000', '%d/%d (%+.1f%%)' % (
                        self.rs2000.change, self.rs2000.open_interest, rs2000_chg
                    )),
                ],
                'energy': [
                    ('oil', '%d/%d (%+.1f%%)' % (
                        self.oil.change, self.oil.open_interest, oil_chg
                    )),
                    ('gas', '%d/%d (%+.1f%%)' % (
                        self.gas.change, self.gas.open_interest, gas_chg
                    )),
                ],
                'metal': [
                    ('gold', '%d/%d (%+.1f%%)' % (
                        self.gold.change, self.gold.open_interest, gold_chg
                    )),
                ],
                'finance': [
                    ('bond30y', '%d/%d (%+.1f%%)' % (
                        self.bond10y.change, self.bond10y.open_interest, bond30y_chg
                    )),
                    ('bond2y', '%d/%d (%+.1f%%)' % (
                        self.bond2y.change, self.bond2y.open_interest, bond2y_chg
                    )),
                ],
                'currency': [
                    ('dollar', '%d/%d (%+.1f%%)' % (
                        self.dollar.change, self.dollar.open_interest, dollar_chg
                    )),
                ],
            }
