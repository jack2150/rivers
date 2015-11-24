from math import exp, sqrt
from QuantLib import *
import numpy as np
import pandas as pd
import re

from pandas.tseries.offsets import BDay


def get_div_yield(df_stock, df_dividend):
    """
    Calculate a series of dividend yield
    :param df_stock: DataFrame
    :param df_dividend: DataFrame
    :return: Series
    """
    df_temp = df_dividend.query(
        '%r <= announce_date <= %r' % (
            df_stock.index[0].strftime('%Y-%m-%d'),
            df_stock.index[-1].strftime('%Y-%m-%d')
        )
    )

    df = pd.DataFrame(range(len(df_stock)), index=df_stock.index)
    df['amount'] = 0.0

    for index, data in df_temp.iterrows():
        df.loc[data['announce_date']:data['expire_date'], 'amount'] = data['amount']

    df['div_yield'] = df['amount'] / df_stock['close']

    return df['div_yield']


class CleanOption(object):
    @staticmethod
    def extract_code(c):
        """
        Extract detail from option code
        :param c: str
        :return: set (str, TimeStamp, str, float)
        """
        symbol = re.search('(^[A-Z]+)\d+[CP]+\d+', c).group(1)
        ex_date = re.search('^[A-Z]+(\d+)[CP]+\d+', c).group(1)
        if len(ex_date) >= 7:
            raise IndexError('skip special/right/split option.')
        ex_date = pd.Timestamp(ex_date[-6:])
        name = Option.Call if re.search('^[A-Z]+\d+([CP]+)\d+', c).group(1) == 'C' else Option.Put

        if '.' in c:
            strike = re.search('^[A-Z]+\d+[CP]+(\d*[.]\d+)', c).group(1)
        else:
            strike = re.search('^[A-Z]+\d+[CP]+(\d+)', c).group(1)

        return symbol, ex_date, name, float(strike)

    def __init__(self, option_code, today, rf_rate, close, bid, ask, impl_vol=0.01, div=0.0):
        """
        Prepare input for option model
        :param option_code: str
        :param today: TimeStamp
        :param rf_rate: float
        :param close: float
        :param impl_vol: float
        :param div: float
        """
        # extract detail from option code
        self.symbol, ex_date, self.name, self.strike = self.extract_code(option_code)

        # not friday ex_date
        if ex_date.weekday() == 5:  # is saturday
            ex_date = ex_date - BDay(1)

        self.ex_date = Date(ex_date.day, ex_date.month, ex_date.year)

        # today date
        self.today = Date(today.day, today.month, today.year)
        #if today >= ex_date:
        #    raise IndexError('last trading day.')

        Settings.instance().evaluationDate = self.today

        # settle date
        settle_day = today + BDay(1)
        if settle_day >= ex_date:
            settle_day = today
        self.settle = Date(settle_day.day, settle_day.month, settle_day.year)  # T+2 settle date

        # risk free rate
        self.rate = rf_rate / 100.0
        self.rf_rate = FlatForward(self.settle, self.rate, Actual365Fixed())

        # expire date
        self.exercise = AmericanExercise(self.settle, self.ex_date)

        # option payoff
        self.payoff = PlainVanillaPayoff(self.name, self.strike)

        # stock price
        self.underlying = SimpleQuote(close)

        # dividend yield: later, using dividend detail and insert
        self.div = div
        self.div_yield = FlatForward(self.settle, self.div, Actual365Fixed())

        # implied volatility, not set yet
        self.impl_vol = impl_vol / 100.0
        self.volatility = BlackConstantVol(self.today, TARGET(), self.impl_vol, Actual365Fixed())

        # process and option
        self.process = BlackScholesMertonProcess(
            QuoteHandle(self.underlying),
            YieldTermStructureHandle(self.div_yield),
            YieldTermStructureHandle(self.rf_rate),
            BlackVolTermStructureHandle(self.volatility)
        )

        self.option = VanillaOption(self.payoff, self.exercise)

        self.time_step = self.ex_date - self.today
        self.grid_point = self.time_step - 1

        # price
        self.ref_value = 0.0

        # black calculator
        self.term = self.time_step / 365.0
        r = self.rate / 100.0
        std = self.impl_vol * sqrt(self.term)
        discount = exp(-r * self.term)
        div_yield = self.div
        spot = self.underlying.value()
        forward = spot * exp((r - div_yield) * self.term)

        self.black_calc = BlackCalculator(
            PlainVanillaPayoff(-1, self.strike), forward, std, discount
        )

        # set before use
        self.bid = bid
        self.ask = ask

    def get_impl_vol(self, assign=False):
        """
        Using bid price calculate the implied volatility
        :return: float
        """
        try:
            impl_vol = self.option.impliedVolatility(self.bid, self.process)

            if assign:
                self.impl_vol = impl_vol
            self.volatility = BlackConstantVol(self.today, TARGET(), impl_vol, Actual365Fixed())

            # process and option
            self.process = BlackScholesMertonProcess(
                QuoteHandle(self.underlying),
                YieldTermStructureHandle(self.div_yield),
                YieldTermStructureHandle(self.rf_rate),
                BlackVolTermStructureHandle(self.volatility)
            )

            self.option = VanillaOption(self.payoff, self.exercise)

        except RuntimeError:
            raise ValueError('impl_vol is 0 or greater than 400%')

        return impl_vol

    def theo_price(self):
        """
        Get theoretical price using quant lib vanilla option
        note: theory price mostly will be lower than ask,
        sometime it was lower than bid too,
        it is rare theory price is higher than big and ask
        but it will occur sometime too
        :rtype : float
        """
        try:
            self.option.setPricingEngine(
                FDAmericanEngine(self.process, self.time_step, self.grid_point)
            )

            value0 = self.option.NPV()
            value1 = self.black_calc.value()

            result = value0
            if value1 > value0:
                result = value1
        except TypeError:
            result = 0.0
            if self.name == Option.Call:
                result = self.underlying.value() - self.strike
                if result < 0:
                    result = 0
            elif self.name == Option.Put:
                result = self.strike - self.underlying.value()
                if result < 0:
                    result = 0

        return round(0.0 if np.isnan(result) else result, 2)

    def greek(self):
        """
        Calculate the greek of this option

        if got intrinsic but no iv, then call is +1, put is -1 delta

        :return: dict
        """
        if self.today < self.ex_date:
            delta = round(self.black_calc.delta(self.underlying.value()), 2)
            gamma = round(self.black_calc.gamma(self.underlying.value()), 2)
            theta = round(self.black_calc.theta(self.underlying.value(), self.time_step), 2)
            vega = round(self.black_calc.vega(self.term) / 100.0, 2)

            intrinsic, _ = self.moneyness()
            if (np.isnan(delta) or delta == 0.0) and intrinsic > 0:
                if self.name == Option.Call:
                    delta = 1
                elif self.name == Option.Put:
                    delta = -1
        else:
            delta = 0
            gamma = 0
            theta = 0
            vega = 0

        return {
            'delta': 0.0 if np.isnan(delta) else delta + 0,  # fix negative zero
            'gamma': 0.0 if np.isnan(gamma) else gamma + 0,
            'theta': 0.0 if np.isnan(theta) else theta + 0,
            'vega': 0.0 if np.isnan(vega) else vega + 0
        }

    def prob(self):
        """
        Calculate the probability of option
        :return: dict
        """
        prob_itm = round(self.black_calc.itmCashProbability() * 100, 2)
        prob_otm = round((1 - self.black_calc.itmCashProbability()) * 100, 2)
        prob_touch = round((1 - self.black_calc.itmCashProbability()) * 2 * 99, 2)

        return {
            'prob_itm': prob_itm,
            'prob_otm': prob_otm,
            'prob_touch': prob_touch,
        }

    def dte(self):
        """
        Calculate the day to expire value
        :return: int
        """
        return self.time_step

    def moneyness(self):
        """
        Calculate option intrinsic and extrinsic value
        :return: (float, float)
        """
        price = (self.bid + self.ask) / 2.0
        if self.name == Option.Call:
            if self.strike > self.underlying.value():
                intrinsic = 0.0
                extrinsic = price
            else:
                intrinsic = self.underlying.value() - self.strike
                extrinsic = round(price - intrinsic, 3)

                if extrinsic < 0:  # no negative extrinsic, old data have
                    extrinsic = 0

            if self.today >= self.ex_date:
                intrinsic = self.theo_price()
                extrinsic = 0

        elif self.name == Option.Put:
            if self.strike < self.underlying.value():
                intrinsic = 0.0
                extrinsic = price
            else:
                intrinsic = self.strike - self.underlying.value()
                extrinsic = round(price - intrinsic, 3)

                if extrinsic < 0:
                    extrinsic = 0.0

            if self.today >= self.ex_date:
                intrinsic = self.theo_price()
                extrinsic = 0
        else:
            raise ValueError('Invalid option name')

        return intrinsic, extrinsic


