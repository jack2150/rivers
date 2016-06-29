import logging
import os
from inspect import getargspec

import numpy as np
import pandas as pd
from itertools import product

from research.algorithm.models import Formula
from research.strategy.models import Commission
from rivers.settings import QUOTE_DIR, RESEARCH_DIR

logger = logging.getLogger('views')


class TradeBacktest(object):
    def __init__(self, symbol, trade):
        """
        :param symbol: str
        :param trade: Trade
        """
        # primary
        self.symbol = symbol.lower()
        self.trade = trade
        logger.info('Trade: %s' % self.trade)
        self.create_order = self.trade.get_method('create_order')
        self.join_data = self.trade.get_method('join_data')

        # formula, previous report, df_signal
        self.formula = Formula()
        self.backtest_id = 0
        self.df_signal = pd.DataFrame()

        # research data
        self.df_stock = pd.DataFrame()
        self.df_contract = pd.DataFrame()
        self.df_option = pd.DataFrame()
        self.df_all = pd.DataFrame()
        self.df_iv = pd.DataFrame()

        # trade data
        self.commission = Commission()
        self.stock_order_fee = 0
        self.option_contract_fee = 0
        self.option_order_fee = 0
        self.capital = 0

        # arguments for loop
        self.args = []
        self.arg_names = [
            a for a in getargspec(self.create_order)[0] if a != 'df_signal'
        ]

        # backtest result
        self.df_trade = pd.DataFrame()

    def set_algorithm(self, formula_id, backtest_id, df_signal):
        """
        Set df_signal into class
        :param formula_id: int
        :param backtest_id: int
        :param df_signal: pd.DataFrame
        """
        self.formula = Formula.objects.get(id=formula_id)
        self.backtest_id = backtest_id

        self.df_signal = df_signal[[
            'date0', 'date1', 'signal0', 'signal1', 'close0', 'close1', 'holding', 'pct_chg'
        ]]
        logger.info('Formula: %s' % self.formula)
        logger.info('backtest_id: %d' % int(self.backtest_id))
        logger.info('df_signal: %d' % len(self.df_signal))

    def set_commission(self, commission_id):
        """
        Set commission object
        :param commission_id: Commission
        """
        self.commission = Commission.objects.get(id=commission_id)
        self.stock_order_fee = float(self.commission.stock_order_fee)
        self.option_contract_fee = float(self.commission.option_contract_fee)
        self.option_order_fee = float(self.commission.option_order_fee)
        logger.info('commission set: %s' % self.commission)

    def set_capital(self, value):
        """
        Set initial capital for trading
        :param value: float
        """
        self.capital = value

    def set_args(self, fields):
        """
        Set arguments that ready for strategy test
        :param fields: dict
        """
        default = {k: v for k, v in self.trade.get_args()}
        args = dict()

        for key in fields.keys():
            # print key, fields[key]
            if ',' in fields[key]:
                args[key] = ['"%s"' % s for s in fields[key].split(',')]
            elif ':' in fields[key]:
                if '.' in fields[key]:
                    # float version
                    data = [float(i) for i in fields[key].split(':')]
                    try:
                        start, stop, step = [float(i) for i in data]
                    except ValueError:
                        start, stop = [float(i) for i in data]
                        step = 0.1

                    args[key] = []
                    i = start
                    while i < stop:
                        args[key].append(i)
                        i = i + step
                else:
                    # int version
                    data = [int(i) for i in fields[key].split(':')]
                    try:
                        start, stop, step = [int(i) for i in data]
                    except ValueError:
                        start, stop = [int(i) for i in data]
                        step = 1

                    args[key] = [int(i) for i in np.arange(start, stop + 1, step)]
            elif type(fields[key]) == tuple:
                # tuple is for string type only
                args[key] = np.array(['"%s"' % f for f in fields[key]])
            else:
                if type(default[key]) == tuple:  # section is tuple
                    args[key] = ['"%s"' % fields[key]]
                else:
                    try:
                        args[key] = [int(fields[key])]
                    except ValueError:
                        raise ValueError('Unable convert {arg} into int'.format(arg=key))

        # make it a list
        keys = sorted(args.keys())
        t = list()
        for key in keys:
            t.append(['%s=%s' % (key, value) for value in args[key]])

        # support multiple variables once
        line = 'dict(%s)' % ','.join(['%s'] * len(t))
        args0 = [eval(line % x) for x in list(product(*t))]

        self.args = args0

        logger.info('Arguments generated, length: %d' % len(self.args))

    def get_data(self):
        """
        Make data frame from objects data
        :return: DataFrame
        """
        start = self.df_signal['date0'].min()
        stop = self.df_signal['date1'].max()

        path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        df_stock = pd.DataFrame()
        for source in ('google', 'yahoo'):
            try:
                df_stock = db.select('stock/%s' % source)
                break
            except KeyError:
                pass
        db.close()

        if len(df_stock) == 0:
            raise LookupError('Symbol < %s > stock not found' % self.symbol.upper())

        self.df_stock = df_stock[start:stop].reset_index()  # slice date range

        logger.info('Seed data, df_stock: %d' % len(self.df_stock))

    def get_extra(self):
        """
        Get extra data that ready for create_order
        """
        args = self.arg_names

        if 'df_contract' in args or 'df_option' in args or 'df_all' in args:
            path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())
            db = pd.HDFStore(path)
            self.df_contract = db.select('option/contract')
            self.df_option = db.select('option/data')
            self.df_iv = db.select('option/iv/day')
            db.close()

            self.df_all = pd.merge(self.df_option, self.df_contract, on='option_code')

            self.set_option_price(50)

            logger.info('Seed df_contract: %d, df_option: %d' % (
                len(self.df_contract), len(self.df_option)
            ))

    def set_option_price(self, percent=50):
        """
        :param percent: int
        :return:
        """
        self.df_all['buy'] = (
            self.df_all['mark'] + (
                (self.df_all['ask'] - self.df_all['mark']) * (percent / 100.0)
            )
        )
        self.df_all['sell'] = (
            self.df_all['mark'] - (
                (self.df_all['mark'] - self.df_all['bid']) * (percent / 100.0)
            )
        )
        self.df_all = self.df_all.round({
            'buy': 2, 'sell': 2
        })

    def create_order(self, df, *args, **kwargs):
        """
        Create order that simulate trade
        :param df: DataFrame
        :param args: *
        :param kwargs: *
        :return: DataFrame
        """
        raise NotImplementedError('Import create order from strategy')

    def calc_stock_qty(self, price, sqm, capital):
        """
        Calculate stock quantity for using capital
        :param price: float
        :param sqm: int
        :param capital: float
        :return: int
        """
        abs_qty = float(abs(sqm))
        qty = np.floor((capital - self.stock_order_fee * 2) / price / abs_qty) * sqm

        return int(qty)

    def calc_option_qty(self, price, oqm, capital):
        """
        Calculate option quantity for using capital
        :param price: float
        :param oqm: int
        :param capital: float
        :return: int
        """
        abs_qty = float(abs(oqm))
        unit_price = (price * 100) + self.option_contract_fee * 2

        if self.option_order_fee:
            qty = (capital - self.option_order_fee * 2) / unit_price / abs_qty
        else:
            qty = capital / unit_price / abs_qty

        return int(np.floor(qty) * oqm)

    def calc_covered_qty(self, price, sqm, oqm, capital):
        """
        Calculate covered quantity with stock and option
        :param price:
        :param sqm:
        :param oqm:
        :param capital:
        :return: int
        """
        unit_price = (price * 100) + self.option_contract_fee * 2
        qty = np.floor((capital - self.stock_order_fee * 2) / unit_price)

        return int(qty * sqm), int(qty * oqm)

    def calc_quantity(self, price, sqm, oqm, capital):
        """
        Calculate quantity for trade
        :param price: float
        :param sqm: int (stock quantity multiplier)
        :param oqm: int (option quantity multiplier)
        :param capital: float
        :return: int, int
        """
        if sqm != 0 and oqm == 0:
            stock_qty = self.calc_stock_qty(price, sqm, capital)
            option_qty = 0
        elif sqm == 0 and oqm != 0:
            stock_qty = 0
            option_qty = self.calc_option_qty(price, oqm, capital)
        else:
            stock_qty, option_qty = self.calc_covered_qty(
                price, sqm, oqm, capital
            )

        return int(stock_qty), int(option_qty)

    @staticmethod
    def calc_amount(price, sqty, oqty, capital):
        """
        Calculate amount for trade and extra capital
        :param price: float
        :param sqty: int
        :param oqty: int
        :param capital: float
        :return: float, float
        """
        if sqty != 0 and oqty == 0:
            amount = price * sqty
        elif sqty == 0 and oqty != 0:
            amount = price * oqty * 100
        else:
            amount = price * sqty

        remain = capital - abs(amount)

        return amount, remain

    def calc_fee(self, sqty, oqty):
        """
        Calculate trading fee
        :param sqty: int
        :param oqty: int
        :return: float
        """
        if sqty != 0 and oqty == 0:
            fee = self.stock_order_fee
        elif sqty == 0 and oqty != 0:
            fee = abs(oqty) * self.option_contract_fee + self.option_order_fee
        else:
            fee = (
                abs(oqty) * self.option_contract_fee +
                self.option_order_fee + self.stock_order_fee
            )

        return fee

    def make_trade(self, **kwargs):
        """
        Generate trade using df_order that ready to report
        :param kwargs: dict
        :return: pd.DataFrame, pd.DataFrame
        """
        if 'df_stock' in self.arg_names:
            kwargs['df_stock'] = self.df_stock
        if 'df_contract' in self.arg_names:
            kwargs['df_contract'] = self.df_contract
        if 'df_all' in self.arg_names:
            kwargs['df_all'] = self.df_all
        if 'df_option' in self.arg_names:
            kwargs['df_option'] = self.df_option

        df_order0 = self.create_order(self.df_signal, **kwargs)
        df_order1 = df_order0.reset_index(drop=True)

        trades = []
        for index, data in df_order1.iterrows():
            sqty0, oqty0 = self.calc_quantity(
                data['close0'], data['sqm0'], data['oqm0'], self.capital
            )

            amount0, remain0 = self.calc_amount(
                data['close0'], sqty0, oqty0, self.capital
            )

            fee0 = self.calc_fee(sqty0, oqty0)

            trade = {
                'sqty0': sqty0,
                'oqty0': oqty0,
                'sqty1': -sqty0,
                'oqty1': -oqty0,
                'amount0': round(amount0, 2),
                'fee0': round(fee0, 2),
                'remain0': round(remain0 - fee0, 2),
                'amount1': data['close1'] * -sqty0,
                'fee1': round(fee0, 2),
            }
            trades.append(trade)

        df_order1 = df_order1[[
            'date0', 'date1', 'signal0', 'signal1', 'close0', 'close1', 'holding'
        ]]
        df_extra = pd.DataFrame(trades)
        df_extra = df_extra[[
            'sqty0', 'sqty1', 'oqty0', 'oqty1',
            'amount0', 'fee0', 'remain0',
            'amount1', 'fee1'
        ]]
        df_trade = pd.concat([df_order1, df_extra], axis=1)
        """:type: pd.DataFrame"""

        df_trade['net_chg'] = np.round((df_trade['amount1'] + df_trade['amount0']) * -1, 2)
        df_trade['remain1'] = (
            df_trade['net_chg'] + np.abs(df_trade['amount0']) +
            df_trade['remain0'] - df_trade['fee1']
        )
        df_trade['pct_chg'] = (df_trade['remain1'] / self.capital) - 1

        return df_order0, df_trade

    @staticmethod
    def profit_loss(df_trade):
        """
        Trade this algorithm every time using fix amount
        Continue trade this algorithm using same amount
        Mean return for trading this algorithm
        :param df_trade: pd.DataFrame
        :return: float, float, float, float
        """
        # calculate pl_sum
        pl_sum = df_trade['pct_chg'].sum()

        # calculate pl_cumprod
        pct_chg = 1 + df_trade['pct_chg']
        """:type: pd.Series"""
        pl_cumprod = pct_chg.cumprod().iloc[-1]

        # calculate pl_mean
        pl_mean = df_trade['pct_chg'].mean()
        pl_std = df_trade['pct_chg'].std()

        return pl_sum, pl_cumprod, pl_mean, pl_std

    @staticmethod
    def trade_summary(df_trade):
        """
        Summary for df_signal pl trade
        :param df_trade: pd.DataFrame
        :return: tuple float
        """
        pl_count = len(df_trade)
        pct_chg = df_trade['pct_chg']
        profit_trade = pct_chg[pct_chg > 0]
        loss_trade = pct_chg[pct_chg < 0]

        profit_count = np.count_nonzero(profit_trade)
        profit_chance = profit_count / float(pl_count)
        loss_count = np.count_nonzero(loss_trade)
        loss_chance = loss_count / float(pl_count)
        profit_max = profit_trade.max()
        profit_min = profit_trade.min()
        loss_max = loss_trade.min()
        loss_min = loss_trade.max()

        return (
            pl_count,
            profit_count, profit_chance,
            loss_count, loss_chance,
            profit_max, profit_min,
            loss_max, loss_min,
        )

    def holding_period(self, df_order):
        """
        Calculate the holding period daily stats
        :param df_order: pd.DataFrame
        :return: list of float
        """
        args = [
            a for a in getargspec(self.join_data)[0]
        ]

        kwargs = {'df_order': df_order}
        for key in ('df_stock', 'df_all', 'df_contract', 'df_option', 'df_iv'):
            if key in args:
                kwargs[key] = getattr(self, key)

        df_list = self.join_data(**kwargs)

        df_join = pd.concat(df_list)
        """:type: pd.DataFrame"""
        pct_chg = df_join['pct_chg']
        profit = pct_chg[pct_chg > 0]
        loss = pct_chg[pct_chg < 0]

        dp_count = len(profit)
        dp_chance = len(profit) / float(len(pct_chg))
        dp_mean = profit.mean()
        dl_count = len(loss)
        dl_chance = len(loss) / float(len(pct_chg))
        dl_mean = loss.mean()

        return dp_count, dp_chance, dp_mean, dl_count, dl_chance, dl_mean

    def report(self, df_order, df_trade):
        """
        Generate a dict report for current formula
        :param df_order: pd.DataFrame
        :param df_trade: pd.DataFrame
        :return: dict
        profit_loss = self.profit_loss()
        trade_summary = self.trade_summary()
        """
        profit_loss = self.profit_loss(df_trade)
        trade_summary = self.trade_summary(df_trade)
        holding_period = self.holding_period(df_order)

        return {
            'pl_sum': profit_loss[0],
            'pl_cumprod': profit_loss[1],
            'pl_mean': profit_loss[2],
            'pl_std': profit_loss[3],
            'pl_count': trade_summary[0],
            'profit_count': trade_summary[1],
            'profit_chance': trade_summary[2],
            'loss_count': trade_summary[3],
            'loss_chance': trade_summary[4],
            'profit_max': trade_summary[5],
            'profit_min': trade_summary[6],
            'loss_max': trade_summary[7],
            'loss_min': trade_summary[8],
            'dp_count': holding_period[0],
            'dp_chance': holding_period[1],
            'dp_mean': holding_period[2],
            'dl_count': holding_period[3],
            'dl_chance': holding_period[4],
            'dl_mean': holding_period[5]
        }

    def generate(self):
        """
        Run all formula args then generate report
        """
        output = '%-6s | %-6s | %-30s'
        logger.info('Trade: %s' % self.trade)
        logger.info('Start generate df_report')

        orders = []
        trades = []
        reports = []
        for key, arg in enumerate(self.args):
            print output % ('BT', key, '%s - %s' % (self.trade.name.upper(), self.trade.path))
            print output % ('BT', 'Args', str(arg))
            df_order, df_trade = self.make_trade(**arg)
            # print df_trade.to_string(line_width=1000)

            # make report
            report = self.report(df_order, df_trade)
            report['date'] = pd.datetime.today().date()
            report['trade'] = str(self.trade.path)
            report['formula'] = str(self.formula.path)
            report['report_id'] = self.backtest_id
            report['args'] = str(arg)

            # df_trade set extra column
            df_trade['date'] = pd.datetime.today().date()
            df_trade['trade'] = str(self.trade.path)
            df_trade['formula'] = str(self.formula)
            df_trade['report_id'] = self.backtest_id
            df_trade['args'] = str(arg)

            # print pd.DataFrame([report]).to_string(line_width=1000)
            orders.append(df_order)
            trades.append(df_trade)
            reports.append(report)

        df_report = pd.DataFrame(reports)
        df_report['date'] = pd.to_datetime(df_report['date'])
        df_report = df_report[[
            'date', 'formula', 'report_id', 'trade', 'args',
            'pl_count', 'pl_sum', 'pl_cumprod', 'pl_mean', 'pl_std',
            'profit_count', 'profit_chance', 'profit_max', 'profit_min',
            'loss_count', 'loss_chance', 'loss_max', 'loss_min',
            'dp_count', 'dp_chance', 'dp_mean', 'dl_count', 'dl_chance', 'dl_mean'
        ]]

        df_trades = pd.concat(trades)
        """:type: pd.DataFrame"""
        df_trades['date'] = pd.to_datetime(df_trades['date'])
        df_trades.reset_index(drop=True, inplace=True)
        df_trades = df_trades[[
            'date', 'formula', 'report_id', 'trade', 'args',
            'date0', 'date1', 'signal0', 'signal1', 'close0', 'close1', 'holding',
            'sqty0', 'sqty1', 'oqty0', 'oqty1', 'amount0', 'fee0', 'remain0', 'amount1',
            'fee1', 'net_chg', 'remain1', 'pct_chg'
        ]]

        return orders, df_trades, df_report

    def save(self, fields, formula_id, backtest_id, commission_id, capital, df_signal):
        """
        Setup all, generate test, then save into db
        :param fields: dict
        :param formula_id: int
        :param backtest_id: int
        :param commission_id: int
        :param capital: int
        :param df_signal: pd.DataFrame
        :return: int
        """
        logger.info('Start backtest formula')

        # set symbol and args
        self.set_commission(commission_id)
        self.set_capital(capital)
        self.set_algorithm(formula_id, backtest_id, df_signal)
        self.set_args(fields)
        self.get_data()
        self.get_extra()

        # generate reports
        orders, df_trades, df_report = self.generate()

        # save
        path = os.path.join(RESEARCH_DIR, '%s.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        # remove old same item
        try:
            db.remove('strategy/report', where='trade == %r' % self.trade.path)
            db.remove('strategy/trade', where='trade == %r' % self.trade.path)
        except NotImplementedError:
            db.remove('strategy/report')
            db.remove('strategy/trade')
        except (KeyError, TypeError):
            pass

        db.append('strategy/report', df_report, format='table', data_columns=True, min_itemsize=100)
        db.append('strategy/trade', df_trades, format='table', data_columns=True, min_itemsize=100)
        db.close()
        logger.info('Backtest save: %s' % path)

        return len(df_report)


# todo: rework save, both df_order, df_trade, no df_list