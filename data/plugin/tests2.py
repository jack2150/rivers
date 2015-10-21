from base.utests import TestUnitSetUp
from option_pricing import *


# find GLD150123C114 for 2014-12-08
class TestOptionPricing(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.pricing = NearestOptionPricing(
            option_code='GLD150123C114', strike=114, date='2014-12-08'
        )

    def test_get_all(self):
        self.pricing.get_all()

        #print self.pricing.options
        print self.pricing.option0c.contract.name

    def test_get_date_nearest(self):
        self.pricing.get_all()
        self.pricing.get_date_nearest()

        #print 'current 0', self.pricing.option0c
        #print 'nearest 0', self.pricing.option0n
        #print 'nearest 1', self.pricing.option1n

        #print self.pricing.nearest0
        #print self.pricing.nearest1

        print self.pricing.option0c.impl_vol
        print self.pricing.option0n.impl_vol
        print self.pricing.option1n.impl_vol

        self.pricing.calc_iv()

