from itertools import product
import numpy as np
import pandas as pd
from quantitative.models import AlgorithmResult
from simulation.models import Strategy, Commission


class StrategyQuant(object):
    def __init__(self, algorithmresult_id, strategy_id, commission_id, capital):
        self.algorithm_result = AlgorithmResult.objects.get(id=algorithmresult_id)
        self.strategy = Strategy.objects.get(id=strategy_id)
        self.commission = Commission.objects.get(id=commission_id)
        self.capital = np.float(capital)

        self.quant = self.algorithm_result.algorithm.make_quant()
        self.quant.args = eval(self.algorithm_result.arguments)
        self.quant.seed_data(self.algorithm_result.symbol)

        # 1 algorithm result only have 1 stock and 1 signal
        self.df_stock = self.quant.handle_data(
            self.quant.data[self.algorithm_result.symbol],
            **self.quant.args['handle_data']
        )

        self.df_signal = self.quant.create_signal(
            self.quant.data[self.algorithm_result.symbol],
            **self.quant.args['create_signal']
        )

        self.args = None

    def set_args(self, fields):
        """
        Set arguments that ready for strategy test
        :param fields: dict
        """
        args = dict()

        for key in fields.keys():
            #print key, fields[key]
            if ':' in fields[key]:
                data = [int(i) for i in fields[key].split(':')]
                try:
                    start, stop, step = [int(i) for i in data]
                except ValueError:
                    start, stop = [int(i) for i in data]
                    step = 1

                args[key] = np.arange(start, stop + 1, step)
            elif type(fields[key]) == tuple:
                # tuple is for string type only
                args[key] = np.array(['"%s"' % f for f in fields[key]])
            else:
                if key in ('order', 'side'):
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

    def calc_fees(self, stock_qty, option_qty):
        """
        Calculate commission fee for each trade
        :param stock_qty: int
        :param option_qty: int
        :return: float
        """
        stock_fees = 0
        if stock_qty:
            stock_fees = self.commission.stock_order_fee

        option_fees = 0
        if option_qty:
            order_fees = 0
            if not stock_fees:
                order_fees = self.commission.option_order_fee

            option_fees = order_fees + (
                option_qty * self.commission.option_contract_fee
            )

        return np.float(stock_fees + option_fees)

    # noinspection PyUnresolvedReferences
    def calc_qty(self, close0, sqm, oqm, capital=0.0):
        """
        s qty 1 o qty 0, s qty 100 o qty 1, s qty 0 o qty 1
        :return:
        """
        if not capital:
            capital = self.capital

        f = np.floor if sqm > 0 else np.ceil

        stock_qty = 0
        option_qty = 0
        if sqm and not oqm:
            stock_qty = np.int(f(capital / close0 / sqm))
        elif sqm and oqm:
            stock_qty = np.int(f(capital / close0 / sqm)) * sqm
            option_qty = np.int(stock_qty / sqm)
        elif not sqm and oqm:
            option_qty = np.int(f(capital / close0 / oqm / 100))

        return stock_qty, option_qty

    @staticmethod
    def calc_capital(close0, sqty0, oqty0):
        """
        Calculate capital for each trade
        :param close0: float
        :param sqty0: int
        :param oqty0: int
        :return: float
        """
        capital = 0.0
        if sqty0 and not oqty0:
            capital = close0 * sqty0
        elif sqty0 and oqty0:
            capital = close0 * sqty0
        elif not sqty0 and oqty0:
            capital = close0 * oqty0 * 100

        return capital

    def make_trade(self, **kwargs):
        """
        Input df_order and output df_trade with capital and commission
        :return: DataFrame
        """
        # make order
        df_order = self.strategy.make_order(self.df_stock, self.df_signal, **kwargs)
        df_trade = df_order.copy()

        # calc fees
        df_trade['fee0'] = df_trade.apply(
            lambda x: self.calc_fees(x['sqm0'], x['oqm0']), axis=1
        )
        df_trade['fee1'] = df_trade.apply(
            lambda x: self.calc_fees(x['sqm1'], x['oqm1']), axis=1
        )

        # calc qty
        df_trade['sqty0'] = df_trade.apply(
            lambda x: self.calc_qty(
                x['close0'], x['sqm0'], x['oqm0'],
                self.capital - x['fee0'] - x['fee1']
            )[0],
            axis=1
        )
        df_trade['oqty0'] = df_trade.apply(
            lambda x: self.calc_qty(
                x['close0'], x['sqm0'], x['oqm0'],
                self.capital - x['fee0'] - x['fee1']
            )[1],
            axis=1
        )
        df_trade['sqty1'] = df_trade['sqty0'] * df_trade['sqm1'] * -1
        df_trade['oqty1'] = df_trade['oqty0'] * df_trade['oqm1'] * -1

        # capital and amount
        df_trade['capital'] = self.capital
        df_trade['amount0'] = df_trade.apply(
            lambda x: self.calc_capital(x['close0'], x['sqty0'], x['oqty0']), axis=1
        )
        df_trade['amount1'] = df_trade.apply(
            lambda x: self.calc_capital(x['close1'], x['sqty0'], x['oqty0']), axis=1
        )

        df_trade['remain'] = (df_trade['capital'] - np.abs(df_trade['amount0'])
                              - df_trade['fee1'] - df_trade['fee0'])

        df_trade['roi'] = (df_trade['amount1'] - df_trade['amount0']
                           - df_trade['fee1'] - df_trade['fee0'])
        df_trade['roi_pct_chg'] = np.round(df_trade['roi'] / df_trade['capital'], 4)

        df_trade.drop(['sqm0', 'sqm1', 'oqm0', 'oqm1'], axis=1, inplace=True)

        # format
        df_trade['capital'] = np.round(df_trade['capital'], 2)
        df_trade['amount0'] = np.round(df_trade['amount0'], 2)
        df_trade['amount1'] = np.round(df_trade['amount1'], 2)
        df_trade['remain'] = np.round(df_trade['remain'], 2)
        df_trade['roi'] = np.round(df_trade['roi'], 2)

        return df_trade

    def make_trade_cumprod(self, **kwargs):
        """
        Make cumprod of df_trade using df_order and args
        :return: DataFrame
        """
        # make order
        df_order = self.strategy.make_order(self.df_stock, self.df_signal, **kwargs)

        # calc fees
        df_order['fee0'] = df_order.apply(
            lambda x: self.calc_fees(x['sqm0'], x['oqm0']), axis=1
        )
        df_order['fee1'] = df_order.apply(
            lambda x: self.calc_fees(x['sqm1'], x['oqm1']), axis=1
        )

        data = dict(
            capital=list(),
            remain=list(),
            sqty0=list(),
            oqty0=list(),
            sqty1=list(),
            oqty1=list(),
            amount0=list(),
            amount1=list(),
            roi=list()
        )

        rolling_cap = self.capital
        for index, trade in df_order.iterrows():
            data['capital'].append(rolling_cap)

            sqty0, oqty0 = self.calc_qty(
                trade['close0'], trade['sqm0'], trade['oqm0'],
                rolling_cap - trade['fee0'] - trade['fee1']
            )
            data['sqty0'].append(sqty0)
            data['oqty0'].append(oqty0)
            data['sqty1'].append(sqty0 * trade['sqm1'] * -1)
            data['oqty1'].append(oqty0 * trade['oqm1'] * -1)

            amount0 = self.calc_capital(trade['close0'], sqty0, oqty0)
            amount1 = self.calc_capital(trade['close1'], sqty0, oqty0)
            roi = amount1 - amount0 - trade['fee0'] - trade['fee1']
            remain = rolling_cap - trade['fee0'] - trade['fee1'] - np.abs(amount0)
            data['remain'].append(remain)
            data['amount0'].append(amount0)
            data['amount1'].append(amount1)
            data['roi'].append(roi)

            rolling_cap = rolling_cap + roi + remain - trade['fee0'] - trade['fee1']
        else:
            df_cumprod = pd.DataFrame(data, index=df_order.index.values)

        df_order['roi_pct_chg'] = np.round(df_cumprod['roi'] / df_cumprod['capital'], 4)
        df_trade = df_order.join(df_cumprod).reindex_axis(
            ['date0', 'date1', 'signal0', 'signal1', 'close0', 'close1', 'holding', 'pct_chg',
             'time1', 'sqm0', 'sqm1', 'oqm0', 'oqm1', 'fee0', 'fee1', 'sqty0', 'oqty0',
             'sqty1', 'oqty1', 'capital', 'amount0', 'amount1', 'remain', 'roi'],
            axis=1
        )
        df_trade.drop(['sqm0', 'sqm1', 'oqm0', 'oqm1'], axis=1, inplace=True)

        # format
        df_trade['capital'] = np.round(df_trade['capital'], 2)
        df_trade['amount0'] = np.round(df_trade['amount0'], 2)
        df_trade['amount1'] = np.round(df_trade['amount1'], 2)
        df_trade['remain'] = np.round(df_trade['remain'], 2)
        df_trade['roi'] = np.round(df_trade['roi'], 2)

        return df_trade

    def report(self, df_trade, df_cumprod):
        """
        Maker report using class df_stock and df_trade
        :param df_trade: DataFrame
        :param df_cumprod: DataFrame
        :return: dict
        """
        report = dict()

        report['capital0'] = self.capital
        report['remain_mean'] = df_trade['remain'].mean()
        report['cp_remain_mean'] = df_cumprod['remain'].mean()

        report['capital1'] = self.capital + df_trade['roi'].sum()
        report['cumprod1'] = self.capital + df_cumprod['roi'].sum()

        report['roi_sum'] = df_trade['roi'].sum()
        report['roi_mean'] = df_trade['roi'].mean()
        report['cp_roi_sum'] = df_cumprod['roi'].sum()
        report['cp_roi_mean'] = df_cumprod['roi'].mean()

        report['fee_sum'] = (df_trade['fee0'] + df_trade['fee1']).sum()
        report['fee_mean'] = (df_trade['fee0'] + df_trade['fee1']).mean()

        report.update(self.quant.report(self.df_stock, df_trade))
        return report

    def make_reports(self):
        """
        Using strategy, capital, commission and different arguments
        to generate a list of report
        :return: list of dict
        """
        if not len(self.args):
            raise ValueError('Set arguments before making reports.')

        reports = list()
        for arg in self.args:
            df_trade = self.make_trade(**arg)
            df_cumprod = self.make_trade_cumprod(**arg)

            # create report
            report = self.report(df_trade, df_cumprod)
            report['df_trade'] = df_trade.to_csv()
            report['df_cumprod'] = df_cumprod.to_csv()

            # add args
            report['arguments'] = arg.__str__()

            # append into list
            reports.append(report)

        return reports
