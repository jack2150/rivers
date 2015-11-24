from django.core.urlresolvers import reverse

from base.tests import TestSetUp
from data.plugin.clean.clean import *
import pandas as pd
from rivers.settings import QUOTE
from QuantLib import *

# prepare data for testing


symbol = 'AIG'
db = pd.HDFStore(QUOTE)
df_rate = db.select('treasury/RIFLGFCY01_N_B')['rate']  # series
df_stock = db.select('stock/thinkback/%s' % symbol.lower())
df_contract = db.select('option/%s/contract' % symbol.lower())
df_option = db.select('option/%s/raw' % symbol.lower())
df_option = df_option.reset_index()
df_dividend = db.select('event/dividend/%s' % symbol.lower())
div_yield = get_div_yield(df_stock, df_dividend)
db.close()


# todo: later test clean class
class TestOptionCalculator(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = symbol

        option_code = 'AIG140517C49'
        today = pd.Timestamp('20140314')
        #rf_rate = self.df_rate.ix[today]['rate']
        rf_rate = 0.12
        #close = self.df_stock.ix[today]['close']
        close = 48.59
        iv = 23.31  # from data

        #self.calc = CleanOption(option_code, today, rf_rate, close, iv)

    def test_get_div_yield(self):
        """
        Test calculate a series of dividend yield

        """
        self.assertEqual(type(div_yield), pd.Series)

        print div_yield[div_yield > 0]

    def test_get_impl_vol(self):
        """
        C | AIG090116P6      |     11 | right: 100, special: Standard, others:
        I | 2009-01-02       | close   1.69 bid   4.25 ask   4.45
        """
        index = pd.Timestamp('20090102')
        calc = CleanOption(
            option_code='AIG090116P6',
            today=index,
            rf_rate=0.5,
            close=1.69,
            impl_vol=10,
            div=0
            # div=d
        )

        print calc.get_impl_vol(4.25)

    def test_extract_code(self):
        """
        Test extract option code detail
        """
        # normal option code
        option_code = 'AIG140517C49'
        result = CleanOption.extract_code(option_code)
        self.assertEqual(result, ('AIG', pd.Timestamp('20140517'), Option.Call, 49.0))
        print option_code, result

        # mini and float strike will raise error
        option_code = 'AIG7140824P49.5'
        self.assertRaises(lambda x: CleanOption.extract_code(option_code))

    def test_get_theo_price(self):
        """
        Test calculate theo price

        """
        df_test = df_option.query('0.2 <= delta <= 0.8').sort('date')

        greater = []
        lesser = []
        div_date = list(div_yield[div_yield > 0].index)

        for _, data in df_test.iterrows():
            index = data['date']

            if index not in div_date:
                continue

            try:
                calc = CleanOption(
                    option_code=data['option_code'],
                    today=index,
                    rf_rate=df_rate[index],
                    close=df_stock.ix[index]['close'],
                    impl_vol=data['impl_vol'],
                    div=div_yield[index]
                    #div=d
                )
                print calc.name
            except IndexError as e:
                print data['option_code'], e.message
                continue

            print '%-15s %s %6.2f %6.2f %6.2f %6.2f | ' % (
                data['option_code'], data['date'].date(),
                df_rate[index], df_stock.ix[index]['close'],
                data['impl_vol'], div_yield[index] * 100.0
            ),

            theo_price = calc.theo_price()

            print 'b: %5.2f, a: %5.2f, tp0: %5.2f, tp1: %5.2f' % (
                data['bid'], data['ask'], data['theo_price'], theo_price
            )

            if data['bid'] >= 0.1 or data['ask'] >= 0.1:
                if data['ask'] >= theo_price:
                    """
                    print 'G: greater than theo price: %6.2f' % (
                        (data['ask'] - theo_price) / theo_price
                    )
                    """
                    greater.append((data['ask'] - theo_price) / theo_price)
                elif theo_price >= data['ask']:
                    """
                    print 'L: less than theo price: %6.2f' % (
                        (theo_price - data['bid']) / theo_price
                    )
                    """
                    lesser.append((theo_price - data['bid']) / theo_price)
                else:
                    raise
                #self.assertGreaterEqual(data['ask'], theo_price)

        print 'greater max: %.2f' % max(greater)
        print 'lesser min: %.2f' % max(lesser)

    def test123(self):
        """
        AIG140517C49
        :return:
        """
        keys = ['delta', 'gamma', 'theta', 'vega']
        keys2 = ['prob_itm', 'prob_otm', 'prob_touch']
        #df_test = self.df_option[self.df_option['delta'] > 0.4].sort('delta').head(1000)
        df_test = self.df_option[
            self.df_option['option_code'] == 'AIG140517C49'
        ].sort_index(ascending=False).head(1000)

        #df_test = self.df_option[self.df_option['delta'] > 0.5].sort(
        #    'delta', ascending=False
        #).head(500)

        #print df_test.to_string(line_width=500)

        for _, data in df_test.iterrows():
            index = data['date']
            print index, data['option_code'],
            print self.df_rate.ix[index]['rate'], self.df_stock.ix[index]['close'], data['impl_vol']
            try:
                calc = CleanOption(
                    data['option_code'],
                    index,
                    self.df_rate.ix[index]['rate'],
                    self.df_stock.ix[index]['close'],
                    data['impl_vol']
                )
                greek = calc.greek()

                #print 'expect:', [(k, data[k]) for k in keys]
                #print 'result:', [(k, greek[k]) for k in keys]
                print 'expect:', [(k, data[k]) for k in keys2]
                print 'result:', [(k, greek[k]) for k in keys2]
                print

                #for k in keys:
                #    self.assertAlmostEqual(data[k], greek[k], 1)
                    # todo: here

                for k in keys2:
                    self.assertAlmostEqual(data[k], greek[k], 0)
            except IndexError:
                pass


    def test_get_dte(self):
        """

        :return:
        """
        #df_call = self.df_contract[self.df_contract['name'] == 'CALL']
        #df_test = pd.merge(self.df_option, df_call, how='inner', on=['option_code'])
        df_put = self.df_contract[self.df_contract['name'] == 'CALL']
        df_test = pd.merge(self.df_option, df_put, how='inner', on=['option_code'])

        df_test = df_test.sort('date')
        #print len(df_call), len(self.df_option), len(df_test)
        #print df_test.head()

        #df_test = self.df_option.sort('delta').head(2000)
        #df_test = self.df_option[self.df_option['delta'] < 0.4].sort('delta').head(1000)
        #df_test = self.df_option[self.df_option['delta'] < 0.4].sort('delta').head(1000)
        #df_test = self.df_option[
        #    self.df_option['option_code'] == 'UZL100220C1'
        #].sort_index().head(100)

        #df_test = self.df_option[self.df_option['delta'] > 0.5].sort(
        #    'delta', ascending=False
        #).head(500)

        #print df_test.to_string(line_width=500)
        # todo: UZL100220C1

        right = 0
        others = 0
        zero = 0
        for _, data in df_test.iterrows():
            # skip split right
            if '/' in data['right']:
                right += 1
                continue

            # skip others
            if len(data['others']):
                others += 1
                continue

            # skip no bid ask
            if not (data['bid'] and data['ask']):
                zero += 1
                continue

            index = data['date']
            print index, data['option_code'],
            print self.df_rate.ix[index]['rate'], self.df_stock.ix[index]['close'], data['impl_vol']
            try:
                calc = CleanOption(
                    data['option_code'],
                    index,
                    self.df_rate.ix[index]['rate'],
                    self.df_stock.ix[index]['close'],
                    data['impl_vol']
                )
                #print data['bid'], data['ask']
                #dte = calc.dte()
                intrinsic, extrinsic = calc.moneyness(data['bid'], data['ask'])
                #intrinsic = calc.intrinsic(data['bid'], data['ask'])

                print 'expect:', data['extrinsic'], data['intrinsic']
                print 'result:', extrinsic, intrinsic

                self.assertAlmostEqual(data['intrinsic'], intrinsic, 1)

                if data['extrinsic'] < 0:
                    self.assertEqual(extrinsic, 0)
                else:
                    self.assertAlmostEqual(data['extrinsic'], extrinsic, 1)


                #if data['dte'] != dte:
                #    print 'expect:', data['dte']
                #    print 'result:', dte
                #    print

                print

                #self.assertEqual(data['dte'], dte, 0)
            except IndexError:
                pass

            #break

        print right, others, zero


class TestCsvToH5(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = symbol

    def test_clean_option(self):
        """
        17m 44s pretty good
        :return:
        """

        # self.client.get(reverse('admin:clean_option', kwargs={'symbol': self.symbol.lower()}))
        self.client.get(reverse('admin:clean_option3', kwargs={'symbol': self.symbol.lower()}))

        #db = pd.HDFStore(QUOTE)
        #df_option = db.select('option/%s/clean' % symbol.lower())
        #db.close()

        #print df_option[2000:3000].to_string(line_width=1000)

        # todo: wrong prob
        # todo: after clean, got wrong rows




