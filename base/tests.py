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
