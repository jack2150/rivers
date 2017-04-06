from base.dj_tests import TestSetUp
from subtool.option.timesale.views import OptionTimeSaleForm


class TestOptionTimeSale(TestSetUp):
    def test_process(self):
        """

        :return:
        """
        form = OptionTimeSaleForm(data={
            'symbol': 'BAC',
            'date': '2016-05-20',
            'raw_data': """
            03:59:57	20 MAY 16 14.5 C	203	.01	CBOE	.00x.02	1.00	--	14.52
            03:59:55	20 MAY 16 14.5 C	100	.01	NYSE	.01x.02	1.00	--	14.515
            03:58:49	3 JUN 16 14.5 C	133	.25	PHLX	.25x.26	.54	20.05%	14.53	Spread
            03:58:49	20 MAY 16 14.5 C	133	.01	PHLX	.01x.02	1.00	--	14.53	Spread
            """,
        })
        print 'form is_valid: %s' % form.is_valid()
        symbol, date, df_result = form.process()

        print 'symbol: %s, date: %s' % (symbol, date.strftime('%Y-%m-%d'))
        print df_result.to_string(line_width=1000)

        self.assertEqual(len(df_result), 2)
        self.assertEqual(len(df_result.columns), 6)
