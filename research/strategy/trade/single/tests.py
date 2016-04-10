from base.utests import TestUnitSetUp  # require
from research.strategy.models import Trade
from research.strategy.trade.single.call_cs import get_cycle_strike
from research.strategy.trade.tests import TestStrategy2
import pandas as pd
import numpy as np


class TestSingleCallCS(TestStrategy2):
    def setUp(self):
        TestStrategy2.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal()
        self.trade = Trade.objects.get(name='Single CALL *CS')
        self.ready_backtest()

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        for side in ('follow', 'long', 'short'):
            kwargs = {'side': side, 'cycle': 0, 'strike': 3}
            df_trade = self.backtest.create_order(
                self.df_signal,
                self.backtest.df_all,
                **kwargs
            )
            print df_trade.to_string(line_width=500)

            print df_trade['pct_chg'].sum()

            break

    def test_join_data(self):
        """
        Test join df_trade data into daily data
        """
        df_trade = self.backtest.create_order(
            self.df_signal,
            self.backtest.df_all,
            **{'side': 'follow', 'cycle': 0, 'strike': 3}
        )

        df_list = self.backtest.join_data(df_trade, self.backtest.df_all, True)

        for df_daily in df_list:
            print df_daily

    def test_expected_return(self):
        """
        Expected Rates of Return, page 183

        :return:
        """
        df_trade = self.backtest.create_order(
            self.df_signal,
            self.backtest.df_all,
            **{'side': 'follow', 'cycle': 0, 'strike': 3}
        )
        df_date = self.backtest.expected_return(df_trade, self.backtest.df_all)

        df_stock = self.backtest.df_stock.copy()
        df_close = df_stock[df_stock.index.isin(df_date['date'])].reset_index()[['date', 'close']]

        df_test = pd.merge(df_date, df_close, on='date')
        df_test2 = df_test[['mark', 'dte', 'impl_vol', 'strike', 'close', 'prob_itm', 'prob_otm']]
        df_test2['c2s'] = df_test2['strike'] - df_test2['close']
        df_test2['p100'] = (df_test2['strike'] + df_test2['mark'] * 2).iloc[0]
        df_test2['p_even'] = (df_test2['strike'] + df_test2['mark']).iloc[0]
        df_test2['p_loss'] = (df_test2['strike']).iloc[0]
        df_test2['std_1'] = np.round(
            df_test2['close'] * df_test2['impl_vol'] / 100.0 * np.sqrt(df_test2['dte'] / 365.0), 2
        )
        from scipy.stats import norm
        """
        df_test2['new_itm'] = df_test2.apply(
            lambda x: (1 - norm.cdf(
                x['strike'], x['close'],
                x['close'] * x['impl_vol'] / 100.0 * np.sqrt(x['dte'] / 365.0)
            )) * 100,
            axis=1
        )
        df_test2['diff'] = df_test2['prob_itm'] - df_test2['new_itm']
        """

        df_test2['p100itm'] = df_test2.apply(
            lambda x: (1 - norm.cdf(
                x['p100'], x['close'],
                x['close'] * x['impl_vol'] / 100.0 * np.sqrt(x['dte'] / 365.0)
            )) * 100,
            axis=1
        )
        df_test2['p100%'] = 1

        df_test2['p_even_itm0'] = df_test2.apply(
            lambda x: (1 - norm.cdf(
                x['p_even'], x['close'],
                x['close'] * x['impl_vol'] / 100.0 * np.sqrt(x['dte'] / 365.0)
            )) * 100,
            axis=1
        )
        df_test2['p_even%'] = 0.5

        df_test2['p_even_itm1'] = df_test2['p_even_itm0'] - df_test2['p100itm']

        df_test2['p_loss_itm0'] = df_test2.apply(
            lambda x: (1 - norm.cdf(
                x['p_loss'], x['close'],
                x['close'] * x['impl_vol'] / 100.0 * np.sqrt(x['dte'] / 365.0)
            )) * 100,
            axis=1
        )
        df_test2['p_loss_itm1'] = df_test2['p_loss_itm0'] - df_test2['p_even_itm0']
        df_test2['p_loss%'] = -0.5

        df_test2['p_maxloss_itm'] = 100 - df_test2['p_loss_itm0']
        df_test2['p_maxloss%'] = -1

        del df_test2['p_even_itm0'], df_test2['p_loss_itm0']

        df_test2['expected_return'] = (
            df_test2['p100itm'] / 100.0 * df_test2['p100%'] +
            df_test2['p_even_itm1'] / 100.0 * df_test2['p_even%'] +
            df_test2['p_loss_itm1'] / 100.0 * df_test2['p_loss%'] +
            df_test2['p_maxloss_itm'] / 100.0 * df_test2['p_maxloss%']
        )



        print df_test2.to_string(line_width=1000)


        # 14.45%,22.61%,77.39%,46.79%
        # todo: p100 and p_even should be mover
        # todo: wrong impl_vol??? use stock impl_vol instead of option iv


    def test123(self):
        #print self.backtest.df_stock

        # same date, same strike difference cycle
        df_date = self.backtest.df_all.query(
            'date == "20150630" & name == "CALL" & strike == 62.5'
        ).sort_values('dte')

        #df_date = self.backtest.df_all.query(
        #    'date == "20150331" & ex_date == "20170120" & name == "CALL"'
        #).sort_values('strike')

        #df_date = self.backtest.df_all.query(
        #    'date == "20150630" & ex_date == "20160115" & name == "CALL"'
        #).sort_values('strike')
        # print df_date.sort_values('strike').to_string(line_width=1000)

        x = []
        y = []
        for i, d in df_date.iterrows():
            if d['impl_vol'] > 0:
                try:
                    #print d['option_code'], d['strike']
                    #x.append(round(self.backtest.df_stock.ix[d['date']]['close'], 2))
                    #x.append(d['strike'])
                    x.append(int(d['dte']))
                    y.append(d['impl_vol'])
                except KeyError:
                    pass

        print x
        print y

        """
        2015-06-30 result: iv 22.98%
        """



class TestSinglePutCS(TestStrategy2):
    def setUp(self):
        TestStrategy2.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal()
        self.trade = Trade.objects.get(name='Single PUT *CS')
        self.ready_backtest()

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        for side in ('follow', 'long', 'short'):
            kwargs = {'side': side, 'cycle': 0, 'strike': 3}
            df_trade = self.backtest.create_order(
                self.df_signal,
                self.backtest.df_all,
                **kwargs
            )
            print df_trade.to_string(line_width=500)

            print df_trade['pct_chg'].sum()

    def test_join_data(self):
        """
        Test join df_trade data into daily data
        """
        df_trade = self.backtest.create_order(
            self.df_signal,
            self.backtest.df_all,
            **{'side': 'follow', 'cycle': 0, 'strike': 0}
        )

        df_list = self.backtest.join_data(df_trade, self.backtest.df_all, True)

        for df_daily in df_list:
            print df_daily
