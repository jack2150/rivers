from data.models import *
import numpy as np
from scipy.stats import norm
from StringIO import StringIO


# noinspection PyMethodMayBeStatic,PyUnresolvedReferences
class Quant(object):
    def __init__(self):
        self.data = None

    def get_rf_return(self):
        """
        Get risk free rate series from db
        :return: Series
        """
        data = list(
            TreasuryInterest.objects.filter(
                treasury__unique_identifier='H15/H15/RIFLGFCY01_N.B'
            ).values()
        )
        df = pd.DataFrame(data)
        df = df.set_index(df['date'])

        return df['interest']

    def make_df(self, symbol):
        """
        Make data frame from objects data
        :param symbol: str
        :return: DataFrame
        """
        df = pd.DataFrame(list(Stock.objects.filter(symbol=symbol).values()))
        df = df.reindex_axis(
            ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume'],
            axis=1
        ).sort(['date'])

        # add earnings
        earnings = [
            e['date_act'] for e in Earning.objects.filter(symbol=symbol).values('date_act')
        ]
        df['earning'] = df['date'].isin(earnings)

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

    def report(self, df_stock, df_signal):
        """
        Using both stock and signal data frame
        create a report for the strategy
        :param df_stock: DataFrame
        :param df_signal: DataFrame
        :return: dict
        """
        df_spy = self.make_df(symbol='SPY')
        df_spy = df_spy.set_index(df_spy['date'])
        spy_return = df_spy['close'].pct_change()
        rf_return = self.get_rf_return() / 100 / 360

        df0 = df_stock.set_index('date')

        buy_hold = 0.0
        data = list()
        for date0, date1 in zip(df_signal['date0'], df_signal['date1']):
            try:
                df_temp = df0.ix[date0:date1][:-1]
                df_temp['pct_chg'] = df_temp['close'].pct_change()
                f = lambda x: x['pct_chg'] * -1 if x['signal'] == 'SELL' else x['pct_chg']
                df_temp['pl'] = df_temp.apply(f, axis=1)
                df_temp['spy_close'] = df_spy['close']
                df_temp['spy_pct_chg'] = spy_return
                df_temp['rf_pct_chg'] = rf_return

                close0 = df_temp['spy_close'][df_temp.index.values[-1]]
                close1 = df_temp['spy_close'][df_temp.index.values[0]]
                buy_hold += (close1 - close0) / close0

                data.append(df_temp.to_csv())
            except ValueError:
                pass  # skip not enough data for date
        else:
            data2 = data[0]
            for d in data[1:]:
                data2 += '\n'.join(d.split('\n')[1:])

        df1 = pd.read_csv(StringIO(data2), index_col=0)
        df1 = df1.dropna()

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

        # return, trade, buy and hold
        trades = df_signal['pct_chg'].count()
        total_pl = df_signal['pct_chg'].sum()
        avg_pl = df_signal['pct_chg'].mean()
        cumprod_pl = np.cumprod(df_signal['pct_chg'] + 1)[df_signal.index.values[-1]]

        max_profit = df_signal['pct_chg'].max()
        max_loss = df_signal['pct_chg'].min()

        first = df_stock.ix[df_signal.index.values[0]]['close']
        last = df_stock.ix[df_signal.index.values[-1]]['close']
        buy_hold = np.round((last - first) / first, 2)

        # value at risk
        mean = df1['pl'].mean()
        std = df1['pl'].std()
        value_at_risk99 = norm.ppf(1 - 0.99, loc=mean, scale=std)
        value_at_risk95 = norm.ppf(1 - 0.99, loc=mean, scale=std)

        # profit loss trade
        profit_trades = df_signal[df_signal['pct_chg'] > 0]['pct_chg'].count()
        loss_trades = df_signal[df_signal['pct_chg'] < 0]['pct_chg'].count()
        profit_prob = profit_trades / df_signal['pct_chg'].count().astype(np.float)
        loss_prob = loss_trades / df_signal['pct_chg'].count().astype(np.float)

        # output report
        return dict(
            sharpe_rf=round(np.float(avg1 / std1), 6),
            sharpe_spy=round(np.float(avg2 / std2), 6),
            sortino_rf=round(np.float(avg1 / downside_risk1), 6),
            sortino_spy=round(np.float(avg2 / downside_risk2), 6),
            buy_hold=buy_hold,
            trades=trades,
            profit_trades=profit_trades,
            profit_prob=round(profit_prob, 2),
            loss_trades=loss_trades,
            loss_prob=round(loss_prob, 2),
            max_profit=round(max_profit, 2),
            max_loss=round(max_loss, 2),
            sum_result=round(total_pl, 2),
            cumprod_result=round(cumprod_pl, 2),
            mean_result=round(avg_pl, 2),
            var_pct99=round(value_at_risk99, 4),
            var_pct95=round(value_at_risk95, 4)
        )

    def handle_data(self, df):
        """
        Add custom column into data that ready for algorithm test
        :param df: DataFrame
        """
        raise NotImplemented('Handle data function is missing.')

    def create_signal(self, df):
        """
        Run formula then generate signal of enter and exit date
        :param df: DataFrame
        """
        raise NotImplemented('Create signal function is missing')
