from django.db.models import Q
from data.models import Option
import numpy as np
import pandas as pd


# noinspection PyTypeChecker
class NearestOptionPricing(object):
    def __init__(self, option_code, strike, date):
        self.option_code = option_code
        self.date0 = None
        self.date1 = pd.datetime.strptime(date, '%Y-%m-%d').date()
        self.strike = strike

        self.option0n = Option()
        self.option0c = Option()
        self.option1n = Option()
        self.option1c = Option()

        self.options = None
        self.nearest0 = None
        self.nearest1 = None

    def get_all(self):
        """
        find all different date option using option code
        :return:
        """
        self.options = Option.objects.filter(
            contract__option_code=self.option_code
        ).order_by('dte').reverse()

        # find nearest date exists
        dates = pd.Series(list([o.date for o in self.options]))
        self.date0 = dates[np.abs(dates - self.date1).min().index][0]

        self.option0c = self.options.get(date=self.date0)

    def get_date_nearest(self):
        """
        find all nearest same date strike options,
        but different cycle or dte
        :return:
        """
        self.nearest0 = Option.objects.filter(
            Q(date=self.date0) & Q(contract__strike=self.strike)
            & Q(contract__special__in=('Standard', 'Weeklys'))
            & Q(contract__name=self.option0c.contract.name)
        ).exclude(id=self.option0c.id).order_by('dte')
        self.nearest1 = Option.objects.filter(
            Q(date=self.date1) & Q(contract__strike=self.strike)
            & Q(contract__special__in=('Standard', 'Weeklys'))
            & Q(contract__name=self.option0c.contract.name)
        ).order_by('dte')

        # find nearest option using
        df = pd.DataFrame([n.dte for n in self.nearest0])
        df[1] = np.abs(df[0] - self.option0c.dte)
        df = df.sort([1])
        dte = df.ix[df.index.values[0]][0]
        self.option0n = self.nearest0.get(dte=dte)
        self.option1n = self.nearest1.get(
            contract__option_code=self.option0n.contract.option_code
        )

    def calc_iv(self):
        """
        calculate iv using same option dif date and same date strike but dif cycle
        :return:
        """
        iv_dif = self.option0c.impl_vol / self.option0n.impl_vol
        new_iv1 = round(self.option1n.impl_vol * iv_dif, 4)

        iv_move = self.option1n.impl_vol / self.option0n.impl_vol
        new_iv2 = round(self.option0c.impl_vol * iv_move, 4)

        print iv_dif, new_iv1

        print iv_move, new_iv2

        print 'exact', (new_iv1 + new_iv2) / 2.0

        # todo: now u can calculate options
        # todo: bid ask spread
        # todo: price within range?
