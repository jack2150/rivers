from django.core.urlresolvers import reverse

from base.tests import TestSetUp


class TestOptionCalculator(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'AIG'

    def test123(self):
        """
        Test fill missing options
        """
        self.client.get(reverse('admin:fillna_option', kwargs={'symbol': self.symbol.lower()}))

