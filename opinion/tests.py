from django.core.urlresolvers import reverse
from base.dj_tests import TestSetUp
from opinion.models import *
from statement.models import Statement


class TestMarketProfile(TestSetUp):
    def test_market_profile(self):
        """

        :return:
        """
        self.client.get(
            reverse('admin:market_profile', kwargs={'date': '2016-03-12'})
        )



























