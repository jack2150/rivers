from base.utests import TestUnitSetUp
from django.core.urlresolvers import reverse


class TestVerifyOptions(TestUnitSetUp):
    def test_verify_options(self):
        """
        100 Standard JAN 10 70.00 PUT WAPMN
        {'date': datetime.date(2009, 1, 2)} {'date': datetime.date(2010, 2, 5)} 186
        100 Standard JAN 10 70.00 PUT AIGMN
        {'date': datetime.date(2009, 6, 16)} {'date': datetime.date(2010, 1, 15)} 147
        # 1 and 2 is exhcange option code and special when split

        100 Standard JAN 10 70.00 PUT IKGMW
        {'date': datetime.date(2009, 8, 7)} {'date': datetime.date(2010, 1, 15)} 110
        # wrong strike price
        ,,.01,.010,.00,.00,.00,.00,,++,0.00%,100.00%,57.27%,0,"1,350",0,.01,IKGAW,0,.02,
        JAN 10,49,20.80,21.00,20.00,20.900,.00,.00,.00,.00,,++,100.00%,0.00%,57.27%,0,328,20.94,-.04,IKGMW,,

        100 Standard JAN 10 70.00 PUT AJUMN
        {'date': datetime.date(2009, 8, 28)} {'date': datetime.date(2010, 1, 15)} 97
        # duplicate option code with 1, same code but different cycle 2012 not 2010
        :return:
        """
        response = self.client.get(reverse('admin:verify_options', kwargs={'symbol': 'AIG'}))

        #print response

        # todo: above problem