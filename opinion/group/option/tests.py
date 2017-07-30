from django.core.urlresolvers import reverse

from base.dj_tests import TestSetUp
from base.ufunc import ts
from opinion.group.option.models import OptionStat, OptionStatTimeSaleContract, OptionStatTimeSaleTrade
from opinion.group.option.views import OptionTimeSaleForm


class TestOptionTimeSale(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'BAC'
        self.date = '2016-05-20'
        self.option_stat = OptionStat(
            symbol=self.symbol,
            date=self.date
        )
        self.option_stat.save()

        self.data = {
            'symbol': self.symbol,
            'date': self.date,
            'raw_data': """
            03:59:57	20 MAY 16 14.5 C	203	.01	CBOE	.00x.02	1.00	--	14.52
            03:59:55	20 MAY 16 14.5 C	100	.01	NYSE	.01x.02	1.00	--	14.515
            03:58:49	3 JUN 16 14.5 C	133	.25	PHLX	.25x.26	.54	20.05%	14.53	Spread
            03:58:49	20 MAY 16 14.5 C	133	.01	PHLX	.01x.02	1.00	--	14.53	Spread
            """,
        }

    def test_process(self):
        """

        :return:
        """
        form = OptionTimeSaleForm(data=self.data)
        print 'form is_valid: %s' % form.is_valid()
        symbol, date, df_result, df_trade = form.process()

        print 'symbol: %s, date: %s' % (symbol, date.strftime('%Y-%m-%d'))
        print ts(df_result)
        print ts(df_trade)

        # self.assertEqual(len(df_result), 2)
        # self.assertEqual(len(df_result.columns), 6)

    def test_create_view(self):
        """

        :return:
        """
        response = self.client.post(reverse('timesale_create', kwargs={
            'obj_id': self.option_stat.id,
        }), data=self.data)

        print 'OptionStatTimeSaleContract'
        for ts_contract in OptionStatTimeSaleContract.objects.all():
            print ts_contract

        print ''
        print 'OptionStatTimeSaleTrade'
        for ts_trade in OptionStatTimeSaleTrade.objects.all():
            print ts_trade

        # print response

    def test_report_view(self):
        """

        :return:
        """
        self.client.post(reverse('timesale_create', kwargs={
            'obj_id': self.option_stat.id,
        }), data=self.data)

        response = self.client.post(reverse('timesale_report', kwargs={
            'obj_id': self.option_stat.id,
        }))

















