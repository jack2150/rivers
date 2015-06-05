from django.db.models import Q
from pandas import DataFrame
from data.models import Stock, Earning, Dividend


class StockManager(object):
    @staticmethod
    def get(symbol, source='yahoo', earning=False, dividend=False):
        """
        Test get stock from db that exclude earning and dividend
        :param symbol: str
        :param source: str ('thinkback', 'google', 'yahoo')
        :param earning: bool
        :param dividend: bool
        :return: Stock
        """
        earning_dates = []
        if not earning:
            earning_dates = [e[0] for e in Earning.objects.filter(symbol=symbol).values_list('date_act')]

        dividend_dates = []
        if not dividend:
            dividend_dates = [d[0] for d in Dividend.objects.filter(symbol=symbol).values_list('expire_date')]

        dates = set(earning_dates + dividend_dates)

        stocks = Stock.objects.filter(
            Q(symbol=symbol) & Q(source=source)
        ).exclude(date__in=dates)

        return stocks

    @staticmethod
    def second(symbol, source='yahoo'):
        """

        :param symbol:
        :param source:
        :return:
        """
        earning_dates = [e[0] for e in Earning.objects.filter(symbol=symbol).values_list('date_act')]

        stocks = Stock.objects.filter(
            Q(symbol=symbol) & Q(source=source)
        )

        # make it df
        df_stocks = DataFrame()
        for stock in stocks:
            df_stocks = df_stocks.append(stock.to_hdf())

        # add columns earnings
        df_stocks['Earning'] = [date in earning_dates for date in df_stocks.index.values]

        return df_stocks


# todo: dividend may also wrong, verify, download all of it