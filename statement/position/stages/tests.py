from base.tests import TestSetUp
from statement.models import Statement, AccountTrade, Position


class TestStage(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        lines = [
            'Net Liquidating Value, "$49,141.69"',
            'Stock Buying Power, "$36,435.34"',
            'Option Buying Power, "$36,435.34"',
            'Commissions / Fees YTD,$159.08',
        ]

        self.statement = Statement()
        self.statement.date = '2015-01-29'
        self.statement.load_csv(lines)
        self.statement.save()

        self.position = None

    def create_position(self, name, spread):
        self.position = Position()

        self.position.name = name
        self.position.spread = spread
        self.position.start = '2015-01-29'
        self.position.save()

    def create_stock_trade(self, side, qty, price, net_price=0, spread='STOCK'):
        line = ',1/29/15 14:40:29,{spread},{side},{qty},' \
               'TO OPEN,SPY,,,ETF,{price},{net_price},LMT'
        line = line.format(
            spread=spread, side=side, qty=qty, price=price,
            net_price=net_price if net_price else price
        )

        account_trade = AccountTrade()
        account_trade.position = self.position
        account_trade.statement = self.statement
        account_trade.load_csv(line)
        account_trade.save()

        return account_trade

    def create_option_trade(self, spread, side, qty, price, net_price, contract,
                            exp='MAR 15', strike=204):
        line = ',1/29/15 14:41:41,{spread},{side},{qty},TO OPEN,TSLA,{exp},' \
               '{strike},{contract},{price},{net_price},LMT'

        line = line.format(
            spread=spread, side=side, qty=qty, exp=exp, strike=strike,
            contract=contract, price=price, net_price=net_price,
        )

        account_trade = AccountTrade()
        account_trade.position = self.position
        account_trade.statement = self.statement
        account_trade.load_csv(line)
        account_trade.save()

        return account_trade
