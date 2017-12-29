from django.core.urlresolvers import reverse

from base.utests import TestUnitSetUp


class TestExcelDatePrice(TestUnitSetUp):
    def test_view(self):
        response = self.client.post(reverse('excel_date_price'), data={
            'symbol': 'LUV',
            'dates': """
                9/13/2016
                8/25/2016
                8/10/2016
                7/27/2016
                7/13/2016
            """
        })


class TestExtractTradeInfo(TestUnitSetUp):
    def test_view(self):
        response = self.client.post(reverse('extract_trade_butterfly'), data={
            'trade': """
                        BUY +3 BUTTERFLY JPM 100 15 SEP 17 85/90/97.5 CALL @.60 LMT
                    """
        })
        print response.context['data']

        response = self.client.post(reverse('extract_trade_butterfly'), data={
            'trade': """
                        SELL -3 BUTTERFLY JPM 100 15 SEP 17 85/90/97.5 CALL @.60 LMT
                    """
        })
        print response.context['data']
