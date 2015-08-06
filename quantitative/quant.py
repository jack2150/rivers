from django.db.models import Q
from data.models import *
from itertools import product
import numpy as np
from scipy.stats import norm
from StringIO import StringIO


class AlgorithmQuant(object):
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.data = None
        self.args = None

    def set_args(self, fields):
        """
        Generate a list of variables
        :param fields: dict Sample {
            'handle_data_span': '120:240:20',
            'handle_data_previous': '20:40:20',
            'create_signal_holding': '30:60:30',
        }
        """
        arguments = self.algorithm.get_args()
        args = dict()

        for arg, default in arguments:
            if type(default) == tuple:
                if fields[arg] in default:
                    args[arg] = ['"%s"' % fields[arg]]
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
                if arg in ('order', 'side'):
                    args[arg] = ['"%s"' % fields[arg]]
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
        make_dict = lambda a, f: {
            k.replace(f + '_', ''): v for k, v in a.items() if f in k
        }

        args1 = list()
        for field in args0:
            args1.append(dict(
                handle_data=make_dict(field, 'handle_data'),
                create_signal=make_dict(field, 'create_signal')
            ))

        self.args = args1

    def handle_data(self, df, *args, **kwargs):
        """
        Handle data that apply algorithm and add new column into stock data
        :param df: DataFrame
        :param args: *
        :param kwargs: *
        :return: DataFrame
        """
        raise NotImplementedError('Import handle data from algorithm.')

    def create_signal(self, df_stock, *args, **kwargs):
        """
        Create signal data frame using algorithm stock data
        :param df_stock: DataFrame
        :param args: *
        :param kwargs: *
        :return: DataFrame
        """
        raise NotImplementedError('Import handle data from algorithm.')

    @staticmethod
    def get_rf_return():
        """
        Get risk free rate series from db
        :return: Series
        """
        data = list(
            TreasuryInterest.objects.filter(
                treasury__unique_identifier='H15/H15/RIFLGFCY01_N.B'
            ).values()
        )

        if not len(data):
            raise LookupError('Risk free rate not found in db.')

        df = pd.DataFrame(data)
        df = df.set_index(df['date'])

        return df['interest']

    @staticmethod
    def make_df(symbol):
        """
        Make data frame from objects data
        :param symbol: str
        :return: DataFrame
        """
        df = pd.DataFrame(list(Stock.objects.filter(
            Q(symbol=symbol) & Q(source='google')
        ).values()))
        df = df.reindex_axis(
            ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume'],
            axis=1
        ).sort(['date'])

        if not df['close'].count():
            raise LookupError('Symbol %s stock not found in db.' % symbol.upper())

        # add earnings
        #earnings = [
        #    e['date_act'] for e in Earning.objects.filter(symbol=symbol).values('date_act')
        #]
        #df['earning'] = df['date'].isin(earnings)

        # change type
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(np.float)

        return df

    def seed_data(self, symbols):
        """
        A method use to generate single symbol data frame
        :param symbols: str
        :return: DataFrame
        """
        if type(symbols) in (str, unicode):
            symbols = [symbols]
        elif type(symbols) != list:
            raise ValueError('Invalid symbol type (str or list of str).')

        data = dict()
        for symbol in symbols:
            # create df
            data[symbol] = self.make_df(symbol)

        self.data = pd.Panel(data)

    @staticmethod
    def max_dd(percents):
        """
        Calculate max drawdown effect
        :param percents: list or Series
        :return: float
        """
        dd_list = []
        max_pct = 0
        for pct in percents:
            if pct > max_pct:
                max_pct = pct

            dd_list.append(pct - max_pct)

        result = 0
        if len(dd_list):
            result = np.round(min(dd_list), 2)

        return result

    @staticmethod
    def create_signal2(df, df_signal):
        """
        Use df and df_signal and add more columns into df_signal
        :param df: DataFrame
        :param df_signal: DataFrame
        :return: DataFrame
        """
        df2 = df_signal.copy()

        # mean or median
        df1 = df.set_index(['date'])
        mean_list = list()
        median_list = list()
        max_list = list()
        min_list = list()
        std_list = list()

        profits = list()
        losses = list()

        for data0, date1, signal in zip(df2['date0'], df2['date1'], df2['signal0']):
            df_temp = df1.ix[data0:date1].copy()
            close = df_temp['close']
            pct_chg = df_temp['close'].pct_change().dropna()

            mean_list.append(close.median())
            median_list.append(close.mean())
            std_list.append(close.std())

            if signal == 'BUY':
                max_list.append(close.max())
                min_list.append(close.min())
                profits.append(pct_chg[pct_chg > 0].count() / np.float(pct_chg.count()))
                losses.append(pct_chg[pct_chg < 0].count() / np.float(pct_chg.count()))
            else:
                max_list.append(close.min())
                min_list.append(close.max())
                losses.append(pct_chg[pct_chg > 0].count() / np.float(pct_chg.count()))
                profits.append(pct_chg[pct_chg < 0].count() / np.float(pct_chg.count()))
        else:
            r = lambda x, y: np.round(((x - y) / y).astype(np.float), 4)

            df2['mean'] = r(mean_list, df2['close0'])
            df2['median'] = r(median_list, df2['close0'])
            df2['max'] = r(max_list, df2['close0'])
            df2['min'] = r(min_list, df2['close0'])
            df2['std'] = np.round((std_list / df2['close0']).astype(np.float), 4)

            # swap max min for buy sell
            df2['max2'] = df2['max']
            df2['min2'] = df2['min']

            # swap pl percent
            df2['p_pct'] = np.round(profits, 2)
            df2['l_pct'] = np.round(losses, 2)

        # format columns
        df2['pct_chg'] = np.round(df2['pct_chg'], 4)
        df2['holding'] = df2['holding'].apply(
            lambda x: int(x.astype('timedelta64[D]') / np.timedelta64(1, 'D'))
        ).astype(np.int)

        return df2

    def report(self, df_stock, df_signal):
        """
        Using both stock and signal data frame
        create a report for the strategy
        :param df_stock: DataFrame
        :param df_signal: DataFrame
        :return: dict
        """
        df_spy = self.make_df(symbol='SPY')
        if not df_spy['close'].count():
            raise LookupError('SPY underlying not found in db.')

        df_spy = df_spy.set_index(df_spy['date'])
        spy_return = df_spy['close'].pct_change()
        rf_return = self.get_rf_return() / 100 / 360

        df0 = df_stock.set_index('date')

        bh_sum = 0.0
        csv_data = list()

        #print df_stock.to_string(line_width=300)

        for index, data in df_signal.iterrows():
            try:
                df_temp = df0.ix[data['date0']:data['date1']]
                if len(df_temp) > 2:
                    df_temp = df_temp[:-1]

                df_temp = df_temp.reindex_axis(
                    ['symbol', 'open', 'high', 'low', 'close', 'volume'], axis=1
                )

                #df_temp = df0.ix[data['date0']:data['date1']][:-1].copy()
                df_temp['pct_chg'] = np.round(df_temp['close'].pct_change(), 4)

                f = lambda x: x['pct_chg'] * -1 if x['signal'] == 'SELL' else x['pct_chg']
                if 'pl' in df_temp.columns:
                    df_temp['pl'] = df_temp.apply(f, axis=1)
                else:
                    df_temp['signal'] = data['signal0']
                    df_temp['pl'] = df_temp.apply(f, axis=1)
                df_temp['spy_close'] = df_spy['close']
                df_temp['spy_pct_chg'] = np.round(spy_return, 4)
                df_temp['rf_pct_chg'] = np.round(rf_return, 4)

                close0 = df_temp['close'][df_temp.index.values[0]]
                close1 = df_temp['close'][df_temp.index.values[-1]]
                bh_sum += (close1 - close0) / close0

                csv_data.append(df_temp.to_csv())

                # fill missing data
                df_temp['pct_chg'] = df_temp['pct_chg'].fillna(0)
                df_temp['pl'] = df_temp['pl'].fillna(0)
                df_temp['spy_close'] = df_temp['spy_close'].ffill()
                df_temp['spy_pct_chg'] = df_temp['spy_pct_chg'].ffill()
                df_temp['rf_pct_chg'] = df_temp['rf_pct_chg'].ffill()
            except ValueError:
                pass  # skip not enough data for date
        else:
            csv_data2 = csv_data[0]
            for d in csv_data[1:]:
                csv_data2 += '\n'.join(d.split('\n')[1:])

        df1 = pd.read_csv(StringIO(csv_data2), index_col=0)
        #print df1.to_string(line_width=300)
        df1 = df1.dropna()  # wait drop nan
        #print df1.to_string(line_width=300)

        # return, trade, buy and hold
        pct_key = 'pct_chg'
        if 'roi_pct_chg' in df_signal.columns:
            pct_key = 'roi_pct_chg'

        duplicated = any(pd.Series(df1.index.values).duplicated())

        # drawdown section
        # max bnh drawdown, wrong
        if duplicated or not df1['pct_chg'].count():
            max_bh_dd = 0.0
            max_dd = 0.0
            r_max_bh_dd = 0.0
            r_max_dd = 0.0

            bh_cumprod = 0.0
            pl_cumprod = 0.0
        else:
            max_bh_dd = self.max_dd(df1['pct_chg'] + 1)

            # max algorithm drawdown
            max_dd = self.max_dd(df1['pl'] + 1)

            if df1['pct_chg'].count() > 20 and df1['pl'].count() > 20:
                # rolling max bnh drawdown
                df1['pct_r_max'] = pd.rolling_max(df1['pct_chg'] + 1, 20)
                df1['pct_r_min'] = pd.rolling_min(df1['pct_chg'] + 1, 20)
                df1['r_pct_dd'] = (df1['pct_r_min'] - df1['pct_r_max']) / df1['pct_r_max']
                r_max_bh_dd = df1['r_pct_dd'].min()

                # rolling max algorithm drawdown
                df1['pl_r_max'] = pd.rolling_max(df1['pl'] + 1, 20)
                df1['pl_r_min'] = pd.rolling_min(df1['pl'] + 1, 20)
                df1['r_pl_dd'] = (df1['pl_r_min'] - df1['pl_r_max']) / df1['pl_r_max']
                r_max_dd = df1['r_pl_dd'].min()
            else:
                r_max_bh_dd = 0.0
                r_max_dd = 0.0

            # buy hold cumprod
            bh_cumprod = np.cumprod(df1['pct_chg'] + 1)[df1.index.values[-1]]
            pl_cumprod = np.cumprod(df_signal[pct_key] + 1)[df_signal.index.values[-1]] - 1

        # sharpe ratio, sortino ratio
        df1['excess_return1'] = df1['pl'] - df1['rf_pct_chg']
        df1['excess_return2'] = df1['pl'] - df1['spy_pct_chg']

        df1['negative_excess_return1'] = df1.apply(
            lambda x: 0.0 if x['excess_return1'] > 0 else x['excess_return1'],
            axis=1
        )
        df1['negative_excess_return2'] = df1.apply(
            lambda x: 0.0 if x['excess_return2'] > 0 else x['excess_return2'],
            axis=1
        )

        downside_risk1 = np.sqrt(
            np.square(df1['negative_excess_return1']).sum() /
            df1['negative_excess_return1'].count().astype(np.float)
        )

        downside_risk2 = np.sqrt(
            np.square(df1['negative_excess_return2']).sum() /
            df1['negative_excess_return2'].count().astype(np.float)
        )

        avg1 = df1['excess_return1'].mean()
        std1 = df1['excess_return1'].std()

        avg2 = df1['excess_return2'].mean()
        std2 = df1['excess_return2'].std()

        trades = df_signal[pct_key].count()
        pl_sum = df_signal[pct_key].sum()
        pl_mean = df_signal[pct_key].mean()
        max_profit = df_signal[pct_key].max()
        max_loss = df_signal[pct_key].min()

        # profit loss trade
        profit_trades = df_signal[df_signal['pct_chg'] > 0]['pct_chg'].count()
        loss_trades = df_signal[df_signal['pct_chg'] < 0]['pct_chg'].count()
        profit_prob = profit_trades / df_signal['pct_chg'].count().astype(np.float)
        loss_prob = loss_trades / df_signal['pct_chg'].count().astype(np.float)

        # value at risk
        mean = df1['pl'].mean()
        std = df1['pl'].std()
        value_at_risk99 = norm.ppf(1 - 0.99, loc=mean, scale=std)
        value_at_risk95 = norm.ppf(1 - 0.95, loc=mean, scale=std)

        # more for signal2
        df_signal2 = self.create_signal2(df_stock, df_signal)
        pct_mean = df_signal2['mean'].median()
        pct_median = df_signal2['median'].median()
        pct_max = df_signal2['max'].median()
        pct_min = df_signal2['min'].median()
        pct_std = df_signal2['std'].median()

        day_profit_mean = df_signal2['p_pct'].mean()
        day_loss_mean = df_signal2['l_pct'].mean()

        # output report
        return dict(
            sharpe_rf=round(np.float(avg1 / std1), 6),
            sharpe_spy=round(np.float(avg2 / std2), 6),
            sortino_rf=round(np.float(avg1 / downside_risk1), 6),
            sortino_spy=round(np.float(avg2 / downside_risk2), 6),
            bh_sum=round(np.float(bh_sum), 2),
            bh_cumprod=np.round(bh_cumprod, 2),
            trades=trades,
            profit_trades=profit_trades,
            profit_prob=round(profit_prob, 2),
            loss_trades=loss_trades,
            loss_prob=round(loss_prob, 2),
            max_profit=round(max_profit, 2),
            max_loss=round(max_loss, 2),
            pl_sum=round(pl_sum, 4),
            pl_cumprod=round(pl_cumprod, 4),
            pl_mean=round(pl_mean, 2),
            var_pct99=round(value_at_risk99, 4),
            var_pct95=round(value_at_risk95, 4),
            max_dd=round(max_dd, 2),
            r_max_dd=round(r_max_dd, 2),
            max_bh_dd=round(max_bh_dd, 2),
            r_max_bh_dd=round(r_max_bh_dd, 2),
            pct_mean=pct_mean,
            pct_median=pct_median,
            pct_max=pct_max,
            pct_min=pct_min,
            pct_std=pct_std,
            day_profit_mean=round(day_profit_mean, 2),
            day_loss_mean=round(day_loss_mean, 2),
        )

    def make_reports(self):
        """
        Using data symbols and all args, generate a list of reports
        :return: list
        """
        if not len(self.data.keys()):
            raise ValueError('Seed data before making reports.')

        if not len(self.args):
            raise ValueError('Set arguments before making reports.')

        reports = list()
        for symbol in self.data.keys():
            for arg in self.args:
                df_stock = self.handle_data(self.data[symbol], **arg['handle_data'])
                df_signal = self.create_signal(df_stock, **arg['create_signal'])

                report = self.report(df_stock, df_signal)

                report['symbol'] = symbol
                report['date'] = pd.datetime.today().date()
                report['algorithm'] = self.algorithm
                report['arguments'] = arg.__str__()
                report['df_signal'] = self.create_signal2(
                    df_stock, df_signal
                ).to_csv()

                reports.append(report)

        return pd.Series(reports)

    def __unicode__(self):
        return 'Algorithm quant: {rule}'.format(
            rule=self.algorithm.rule
        )

    __repr__ = __str__ = __unicode__
