import logging
import os
import numpy as np
import pandas as pd
from data.models import Underlying
from itertools import product
from inspect import getargspec
from scipy.stats import norm
from rivers.settings import QUOTE_DIR, RESEARCH_DIR, SPY_DIR, TREASURY_DIR

logger = logging.getLogger('views')


def dtype(var):
    """
    :param var:
    :return:
    """
    try:
        if float(var) == int(var):
            result = int(var)
        else:
            result = float(var)
    except ValueError:
        result = str(var)

    return result


class FormulaBacktest(object):
    def __init__(self, formula):
        """
        :param formula: Formula
        """
        self.formula = formula
        self.data = None
        self.fields = ''
        self.args = list()

        self.symbol = ''
        self.start = None
        self.stop = None

        self.df_stock = pd.DataFrame()
        self.df_thinkback = pd.DataFrame()
        self.df_change = pd.DataFrame()

        self.df_signal = pd.DataFrame()
        self.df_list = pd.DataFrame()
        self.df_join = pd.DataFrame()

        self.df_earning = pd.DataFrame()
        self.df_dividend = pd.DataFrame()
        self.df_contract = pd.DataFrame()
        self.df_option = pd.DataFrame()
        self.df_all = pd.DataFrame()

        self._handle_data = None
        self._create_signal = None
        self.hd_args = []
        self.cs_args = []

    @staticmethod
    def make_dict(args, func):
        """
        Make a dict for arguments
        :param args: list
        :param func: str
        :return: dict
        """
        result = {}
        for key, value in args.items():
            if func in key:
                result[key.replace(func + '_', '')] = value

        return result

    def set_symbol_date(self, symbol, start=None, stop=None):
        """
        :param symbol: str
        :param start: str or datetime
        :param stop: str or datetime
        """
        # set class property
        self.symbol = symbol.lower()
        self.start = start
        self.stop = stop

    def set_args(self, fields):
        """
        Generate a list of variables
        :param fields: dict Sample {
            'handle_data_span': '120:240:20',
            'handle_data_previous': '20:40:20',
            'create_signal_holding': '30:60:30',
        }
        """
        self.fields = fields
        arguments = self.formula.get_args()
        args = dict()

        for arg, default in arguments:
            if type(default) == tuple:

                if fields[arg] in default:
                    args[arg] = ['"%s"' % fields[arg]]
                elif fields[arg] == 'all':
                    args[arg] = ['"%s"' % a for a in default]
                else:
                    raise ValueError('')
            elif ':' in fields[arg]:
                data = [int(i) for i in fields[arg].split(':')]
                try:
                    start, stop, step = [int(i) for i in data]
                except ValueError:
                    start, stop = [int(i) for i in data]
                    step = 1

                args[arg] = np.arange(start, stop + 1, step)
            else:
                if '.' in fields[arg]:
                    try:
                        args[arg] = [float(fields[arg])]
                    except ValueError:
                        raise ValueError('Unable convert {arg} into float'.format(arg=arg))
                else:
                    try:
                        args[arg] = [int(fields[arg])]
                    except ValueError:
                        raise ValueError('Unable convert {arg} into int'.format(arg=arg))

        # make it a list
        keys = sorted(args.keys())
        t = list()
        for key in keys:
            t.append(['%s=%s' % (key, value) for value in args[key]])

        # support multiple variables once
        line = 'dict(%s)' % ','.join(['%s'] * len(t))
        args0 = [eval(line % x) for x in list(product(*t))]

        # get method name from value keys
        args1 = list()
        for field in args0:
            args1.append(dict(
                handle_data=self.make_dict(field, 'handle_data'),
                create_signal=self.make_dict(field, 'create_signal')
            ))

        self.args = args1

        logger.info('Set arguments, length: %d' % len(args1))

    def set_hd_cs(self, handle_data, create_signal):
        """

        :param handle_data: method
        :param create_signal: method
        """
        self._handle_data = handle_data
        self._create_signal = create_signal

        self.hd_args = getargspec(handle_data)[0]
        self.cs_args = getargspec(create_signal)[0]

    def handle_data(self, *args, **kwargs):
        """
        Handle data that apply algorithm and add new column into stock data
        :param args: *
        :param kwargs: *
        :return: DataFrame
        """
        if self._handle_data:
            df = self._handle_data(*args, **kwargs)
        else:
            raise NotImplementedError('Import handle data from algorithm.')

        return df

    def create_signal(self, *args, **kwargs):
        """
        Create signal data frame using algorithm stock data
        :param args: *
        :param kwargs: *
        :return: DataFrame
        """
        if self._handle_data:
            df = self._create_signal(*args, **kwargs)
        else:
            raise NotImplementedError('Import create_signal from algorithm.')

        return df

    def get_data(self):
        """
        Make data frame from objects data
        :return: DataFrame
        """
        symbol = self.symbol
        start = self.start
        stop = self.stop

        underlying = Underlying.objects.get(symbol=symbol.upper())
        if not start:
            start = underlying.start_date
            self.start = start
        if not stop:
            stop = underlying.stop_date
            self.stop = stop

        path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        df_stock = pd.DataFrame()

        for source in ('google', 'yahoo'):
            try:
                df_stock = db.select('stock/%s' % source)
                break
            except KeyError:
                pass

        if len(df_stock) == 0:
            raise LookupError('Symbol < %s > stock not found (Google/Yahoo)' % symbol.upper())

        if 'df_thinkback' in self.hd_args + self.cs_args:
            df_think = db.select('stock/thinkback')
        else:
            df_think = df_stock

        df_stock = df_stock[start:stop]  # slice date range
        df_stock = df_stock[df_stock.index.isin(df_think.index)]  # make sure in thinkback
        db.close()

        # open spy db
        db = pd.HDFStore(SPY_DIR)
        df_spy = db.select('stock/google')
        df_spy = df_spy[start:stop]
        db.close()

        # open treasury db
        treasury_path = os.path.join(TREASURY_DIR)
        db = pd.HDFStore(treasury_path)
        df_rate = db.select('RIFLGFCY01_N_B')
        df_rate = df_rate[start:stop]
        db.close()

        # sync data, make sure all date is same
        df_stock = df_stock[~df_stock.index.isin(
            d for d in df_stock.index if d not in df_rate.index or d not in df_spy.index
        )]

        df_spy = df_spy[df_spy.index.isin(df_stock.index)]
        df_rate = df_rate[df_rate.index.isin(df_stock.index)]

        self.df_stock = df_stock.reset_index().copy()
        """:type: pd.DataFrame"""

        self.df_change = df_stock.copy()
        """:type: pd.DataFrame"""

        # calculate risk free rate by year
        self.df_change['rate'] = df_rate['rate']
        df_list = []
        for year in range(df_stock.index[0].year, df_stock.index[-1].year + 1):
            df_year = df_rate['%s0101' % year:'%s1231' % year].copy()
            df_year['chg'] = df_year['rate'] / 100.0 / float(len(df_year))

            df_list.append(df_year)
        df_rate = pd.concat(df_list)
        """:type: pd.DataFrame"""
        self.df_change['chg1'] = df_rate['chg']

        # s&p 500 will calculate after trade
        self.df_change['spy'] = df_spy['close']
        self.df_change = self.df_change.dropna()

        logger.info('Seed data, df_stock: %d, df_change: %d' % (
            len(self.df_stock), len(self.df_change)
        ))

    def extra_data(self):
        """
        Add extra data that require for testing
        can continue add more data
        df_earning: earning
        df_dividend: dividend
        df_contract, df_option, df_all: option data
        """
        args = set(self.hd_args + self.cs_args)

        # check which data is require
        path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        if 'df_earning' in args:
            self.df_earning = db.select('event/earning')

        if 'df_dividend' in args:
            self.df_dividend = db.select('event/dividend')

        if 'df_thinkback' in args:
            self.df_thinkback = db.select('stock/thinkback')
            self.df_thinkback = self.df_thinkback.reset_index()

        if 'df_contract' in args or 'df_option' in args or 'df_all' in args:
            self.df_contract = db.select('option/contract')
            self.df_option = db.select('option/data', where='date >= %r & date <= %r' % (
                self.start, self.stop
            ))
            self.df_all = pd.merge(self.df_option, self.df_contract, on='option_code')

            self.df_all = self.df_all[~self.df_all['date'].isin(
                np.setdiff1d(self.df_all['date'].unique(), self.df_stock['date'])
            )]

        db.close()

    def set_signal(self, df_signal):
        """
        Set df_signal into class property
        :param df_signal: pd.DataFrame
        """
        self.df_signal = df_signal.copy()

    def prepare_join(self):
        """
        Generate a list of backtest trade dataframe
        :return: float, float
        """
        df_list = []
        for index, data in self.df_signal.iterrows():
            # print data['signal0'], data['date0'], data['date1']

            df = self.df_change[data['date0']:data['date1']].copy()
            """:type: pd.DataFrame"""

            # close percent change
            df['chg0'] = df['close'].pct_change()
            if data['signal0'] == 'SELL':
                df['chg0'] *= -1

            # set rate is 0
            df.loc[df.index[0], 'chg1'] = 0

            # spy percent change
            df['chg2'] = df['spy'].pct_change()

            df = df.fillna(value=0)
            df = df[[
                'open', 'high', 'low', 'close', 'volume', 'rate', 'spy', 'chg0', 'chg1', 'chg2'
            ]]

            # append into list
            df_list.append(df)

            # print df.to_string(line_width=1000)

        if len(df_list):
            self.df_list = df_list
            """:type: pd.DataFrame"""
            self.df_join = pd.concat(df_list)
            """:type: pd.DataFrame"""
            self.df_join = self.df_join.sort_index()

    def sharpe_ratio(self):
        """
        Calculate sharpe ratio for df_signal
        :return: (float, float)
        """
        df_join = self.df_join.copy()
        """:type: pd.DataFrame"""
        # excess return
        df_join['ex1'] = df_join['chg0'] - df_join['chg1']  # vs risk free
        df_join['ex2'] = df_join['chg0'] - df_join['chg2']  # vs spy

        try:
            sr1 = df_join['ex1'].mean() / df_join['ex1'].std()
        except ZeroDivisionError:
            sr1

        try:
            sr2 = df_join['ex2'].mean() / df_join['ex2'].std()
        except ZeroDivisionError:
            sr2 = 0

        return sr1, sr2

    def sortino_ratio(self):
        """
        Calculate sortino ratio for df_signal
        :return: float, float
        """
        df_join = self.df_join.copy()
        """:type: pd.DataFrame"""
        # excess return
        df_join['ex1'] = df_join['chg0'] - df_join['chg1']  # vs risk free
        df_join['ex2'] = df_join['chg0'] - df_join['chg2']  # vs spy
        
        # negative excess return
        df_join['-ex1'] = df_join['ex1'].apply(lambda r: 0.0 if r > 0 else r)
        df_join['-ex2'] = df_join['ex2'].apply(lambda r: 0.0 if r > 0 else r)

        # downside risk
        dr1 = np.sqrt(
            np.square(df_join['-ex1']).sum() / df_join['-ex1'].count().astype('float')
        )
        dr2 = np.sqrt(
            np.square(df_join['-ex2']).sum() / df_join['-ex2'].count().astype('float')
        )

        sr1 = df_join['ex1'].mean() / dr1
        sr2 = df_join['ex2'].mean() / dr2

        return sr1, sr2

    def buy_hold(self):
        """
        Buy and hold sum of profit for trading period
        :return: float
        """
        return (self.df_join['close'][-1] / self.df_join['close'][0]) - 1

    def profit_loss(self):
        """
        Trade this algorithm every time using fix amount
        Continue trade this algorithm using same amount
        Mean return for trading this algorithm
        :return: float, float, float, float
        """
        # calculate pl_sum
        pl_sum = self.df_signal['pct_chg'].sum()

        # calculate pl_cumprod
        pct_chg = 1 + self.df_signal['pct_chg']
        """:type: pd.Series"""
        pl_cumprod = pct_chg.cumprod().iloc[-1]

        # calculate pl_mean
        pl_mean = self.df_signal['pct_chg'].mean()
        pl_std = self.df_signal['pct_chg'].std()

        return pl_sum, pl_cumprod, pl_mean, pl_std

    def trade_summary(self):
        """
        Summary for df_signal pl trade
        :return: tuple float
        """
        pl_count = len(self.df_signal)
        pct_chg = self.df_signal['pct_chg']
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

    def value_at_risk(self):
        """
        Calculate VaR 99 and 95
        :return: float, float
        """
        mean = self.df_join['chg0'].mean()
        std = self.df_join['chg0'].std()
        var99 = norm.ppf(1 - 0.99, loc=mean, scale=std)
        var95 = norm.ppf(1 - 0.95, loc=mean, scale=std)

        return var99, var95

    def max_draw_down(self):
        """
        Calculate max draw down effect
        :return: float
        """
        df_join = self.df_join.copy()
        """:type: pd.DataFrame"""

        peak = [df_join['close'][0]]
        for index, data in df_join[1:].iterrows():
            if data['close'] > peak[len(peak) - 1]:
                peak.append(data['close'])
            else:
                peak.append(peak[len(peak) - 1])
        df_join['peak'] = peak
        df_join['dd'] = (df_join['close'] - df_join['peak']) / df_join['peak']
        # print df_join.to_string(line_width=1000)

        return df_join['dd'].min()

    def holding_period(self):
        """
        Calculate the holding period daily stats
        :return: list of float
        """
        df_join = self.df_join.copy()
        """:type: pd.DataFrame"""
        pct_chg = df_join['chg0']
        profit = pct_chg[pct_chg > 0]
        loss = pct_chg[pct_chg < 0]

        dp_count = len(profit)
        dp_chance = len(profit) / float(len(pct_chg))
        dp_mean = profit.mean()
        dl_count = len(loss)
        dl_chance = len(loss) / float(len(pct_chg))
        dl_mean = loss.mean()

        return dp_count, dp_chance, dp_mean, dl_count, dl_chance, dl_mean

    def report(self, df_signal):
        """
        Generate a dict report for current formula
        :param df_signal: pd.DataFrame
        :return: dict
        """
        self.set_signal(df_signal)
        self.prepare_join()
        sharpe_ratio = self.sharpe_ratio()
        sortino_ratio = self.sortino_ratio()
        buy_hold = self.buy_hold()
        profit_loss = self.profit_loss()
        trade_summary = self.trade_summary()
        var99, var95 = self.value_at_risk()
        max_dd = self.max_draw_down()
        holding_period = self.holding_period()

        # make report
        return {
            'sharpe_rf': sharpe_ratio[0],
            'sharpe_spy': sharpe_ratio[1],
            'sortino_rf': sortino_ratio[0],
            'sortino_spy': sortino_ratio[1],
            'buy_hold': buy_hold,
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
            'var_99': var99,
            'var_95': var95,
            'max_dd': max_dd,
            'dp_count': holding_period[0],
            'dp_chance': holding_period[1],
            'dp_mean': holding_period[2],
            'dl_count': holding_period[3],
            'dl_chance': holding_period[4],
            'dl_mean': holding_period[5]
        }

    def ready_hd_args(self, args, df_stock):
        """
        Ready handle_data arguments
        :param args: list
        :param df_stock: pd.DataFrame
        :return: list
        """
        temp = {k: v for k, v in args.items()}
        needed = [k for k in self.hd_args if k not in temp.keys()]

        temp.update(
            {k: df_stock if k == 'df' else getattr(self, k) for k in needed}
        )

        return temp

    def ready_cs_args(self, args, df_hd):
        """
        Ready create_signal arguments
        :param args: list
        :param df_hd: pd.DataFrame
        :return: list
        """
        temp = {k: v for k, v in args.items()}
        needed = [k for k in self.cs_args if k not in temp.keys()]

        temp.update(
            {k: df_hd if k == 'df' else getattr(self, k) for k in needed}
        )

        return temp

    @staticmethod
    def min_args(arg):
        """
        Minimize arguments that only show values
        :param arg: dict
        :return: str
        """
        arg_str = []
        for name in sorted(arg.keys()):
            arg_str.append(str(arg[name]))
        return ','.join(arg_str)

    def generate(self):
        """
        Run all formula args then generate report
        """
        output = '%-6s | %-6s | %-30s'
        logger.info('Start generate df_report')

        reports = []
        signals = []
        for key, arg in enumerate(self.args):
            print output % ('BT', key, '%s - %s' % (self.formula.rule.upper(), self.formula.path))
            print output % (
                'BT', 'Args', str(arg).replace('handle_data', 'hd').replace('create_signal', 'cs')
            )
            df_stock = self.df_stock.copy()

            # analysis
            hd_args = self.ready_hd_args(arg['handle_data'], df_stock)
            df_hd = self.handle_data(**hd_args)
            cs_args = self.ready_cs_args(arg['create_signal'], df_hd)
            df_signal = self.create_signal(**cs_args)

            if len(df_signal) == 0:
                continue

            # make report
            report = self.report(df_signal)
            report['date'] = pd.datetime.today().date()
            report['start'] = self.start
            report['stop'] = self.stop
            report['formula'] = str(self.formula.path)

            report['hd'] = self.min_args(arg['handle_data'])
            report['cs'] = self.min_args(arg['create_signal'])
            print output % ('BT', 'Report', 'pl_count: %d, pl_mean: %.2f, profit_chance: %.2f' % (
                report['pl_count'], report['pl_mean'], report['profit_chance']
            ))
            reports.append(report)

            # update signal
            df_signal['date'] = pd.datetime.today().date()
            df_signal['start'] = self.start
            df_signal['stop'] = self.stop
            df_signal['formula'] = str(self.formula.path)
            df_signal['hd'] = self.min_args(arg['handle_data'])
            df_signal['cs'] = self.min_args(arg['create_signal'])

            signals.append(df_signal)

            # print pd.DataFrame([report]).to_string(line_width=1000)
            # break

        if len(reports):
            df_report = pd.DataFrame(reports)
            df_report['date'] = pd.to_datetime(df_report['date'])

            df_report['start'] = pd.to_datetime(df_report['start'])
            df_report['stop'] = pd.to_datetime(df_report['stop'])
            df_report = df_report[[
                'date', 'formula', 'hd', 'cs', 'start', 'stop',
                'sharpe_rf', 'sharpe_spy', 'sortino_rf', 'sortino_spy',
                'buy_hold', 'pl_count', 'pl_sum', 'pl_cumprod', 'pl_mean', 'pl_std',
                'dp_count', 'dp_chance', 'dp_mean', 'dl_count', 'dl_chance', 'dl_mean',
                'profit_count', 'profit_chance', 'profit_max', 'profit_min',
                'loss_count', 'loss_chance', 'loss_max', 'loss_min',
                'var_95', 'var_99', 'max_dd'
            ]]
            df_report = df_report.fillna(0)

            df_signals = pd.concat(signals)
            """:type: pd.DataFrame"""
            df_signals = df_signals[[
                'formula', 'hd', 'cs', 'date', 'start', 'stop',
                'date0', 'date1', 'signal0', 'signal1', 'close0', 'close1',
                'holding', 'pct_chg'
            ]]

            df_signals['date'] = pd.to_datetime(df_signals['date'])
            df_signals['start'] = pd.to_datetime(df_signals['start'])
            df_signals['stop'] = pd.to_datetime(df_signals['stop'])
            df_signals.reset_index(drop=True, inplace=True)

            logger.info('Complete generate df_report')
        else:
            df_report = pd.DataFrame()
            df_signals = pd.DataFrame()

        return df_report, df_signals

    def save(self, fields, symbol, start=None, stop=None):
        """
        Setup all, generate test, then save into db
        :param fields: dict
        :param symbol: str
        :param start: str or datetime
        :param stop: str or datetime
        :return: int
        """
        logger.info('Start backtest formula')

        # set symbol and args
        self.set_symbol_date(symbol, start, stop)
        self.set_args(fields)
        self.get_data()
        self.extra_data()

        # generate reports
        df_report, df_signal = self.generate()

        # format
        report_keys = [
            'date', 'formula', 'hd', 'cs', 'start', 'stop', 'sharpe_rf', 'sharpe_spy', 'sortino_rf',
            'sortino_spy', 'buy_hold', 'pl_count', 'pl_sum', 'pl_cumprod', 'pl_mean', 'pl_std', 'dp_count',
            'dp_chance', 'dp_mean', 'dl_count', 'dl_chance', 'dl_mean', 'profit_count', 'profit_chance',
            'profit_max', 'profit_min', 'loss_count', 'loss_chance', 'loss_max', 'loss_min', 'var_95',
            'var_99', 'max_dd'
        ]
        for key in report_keys:
            if key in ('date', 'start', 'stop'):
                # df_report[key] = pd.to_datetime(df_report[key])
                pass
            elif key in ('formula', 'hd', 'cs'):
                # df_report[key] = pd.to_datetime(df_report[key])
                pass
            elif key in ('pl_count', 'dp_count', 'dl_count', 'profit_count', 'loss_count'):
                df_report[key] = df_report[key].astype('int')
            else:
                df_report[key] = df_report[key].astype('float')

        signal_keys = [
            'formula', 'hd', 'cs', 'date', 'start', 'stop', 'date0', 'date1', 'signal0', 'signal1', 'close0',
            'close1', 'holding', 'pct_chg']

        for key in signal_keys:
            if key in ('date', 'start', 'stop', 'date0', 'date1', 'holding'):
                # df_report[key] = pd.to_datetime(df_report[key])
                pass
            elif key in ('formula', 'hd', 'cs', 'signal0', 'signal1'):
                # df_report[key] = pd.to_datetime(df_report[key])
                pass
            else:
                df_signal[key] = df_signal[key].astype('float')

        # save
        if len(df_report):
            path = os.path.join(RESEARCH_DIR, '%s.h5' % symbol.lower())
            db = pd.HDFStore(path)

            # remove old same item
            try:
                db.remove('algorithm/report', where='formula == %r' % self.formula.path)
                db.remove('algorithm/signal', where='formula == %r' % self.formula.path)
            except NotImplementedError:
                db.remove('algorithm/report')
                db.remove('algorithm/signal')
            except KeyError:
                pass

            db.append('algorithm/report', df_report,
                      format='table', data_columns=True, min_itemsize=100)
            db.append('algorithm/signal', df_signal,
                      format='table', data_columns=True, min_itemsize=100)
            db.close()
            logger.info('Backtest save: %s' % path)
        else:
            logger.info('Empty df_report to save')

        return len(df_report)
