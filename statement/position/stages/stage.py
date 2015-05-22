from django.db.models import Q


class Stage(object):
    def __init__(self, trades):
        self.trades = trades
        """:type: QuerySet"""

        # long stock
        self.buy_stocks = self.trades.filter(
            (Q(contract='STOCK') | Q(contract='ETF')) & Q(side='BUY') & Q(qty__gt=0)
        ).all()

        # short stock
        self.sell_stocks = self.trades.filter(
            (Q(contract='STOCK') | Q(contract='ETF')) & Q(side='SELL') & Q(qty__lt=0)
        ).all()

        # long call
        self.buy_calls = self.trades.filter(
            Q(side='BUY') & Q(contract='CALL') & Q(qty__gt=0)
        ).all()

        # naked call
        self.sell_calls = self.trades.filter(
            Q(side='SELL') & Q(contract='CALL') & Q(qty__lt=0)
        ).all()

        # long put
        self.buy_puts = self.trades.filter(
            Q(side='BUY') & Q(contract='PUT') & Q(qty__gt=0)
        ).all()

        # naked put
        self.sell_puts = self.trades.filter(
            Q(side='SELL') & Q(contract='PUT') & Q(qty__lt=0)
        ).all()




