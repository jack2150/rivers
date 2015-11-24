from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from checklist.models import *
from statement.models import Statement


class TestEnterOpinion(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.enter_opinion = EnterOpinion(**{
            'symbol': 'WFC',
            'date': '2015-08-12',

            'score': 3,
            'complete': False,
            'trade': False,

            'risk_profile': 'LOW',
            'bp_effect': 3500.0,
            'profit': 1000.0,
            'loss': 3500.0,
            'size': 10,

            'iv_rank': 19.3,
            'strategy': 'LONG CALL VERTICAL',
            'optionable': True,
            'spread': 'DEBIT',
            'enter_date': '2015-10-31',
            'exit_date': '2015-12-25',
            'dte': 45,

            'signal': 'BULL',
            'event': False,
            'significant': True,
            'confirm': True,
            'target': 99,
            'market': 'MAJOR',
            'description': '',

            'earning': False,
            'dividend': False,
            'split': False,
            'announcement': False,

            'news_level': 'WEAK',
            'news_signal': 'UNKNOWN',

            'long_trend0': 'RANGE',
            'long_trend1': 'BULL',
            'short_trend0': 'BEAR',
            'short_trend1': 'BULL',
            'long_persist': True,
            'short_persist': True
        })
        self.enter_opinion.save()
        self.assertTrue(self.enter_opinion.id)

    def test_get_ownership(self):
        """
        Test get ownership data from nasdaq html file
        """
        self.skipTest('Test only when need')
        self.enter_opinion.get_ownership()
        
        keys = [
            'ownership',
            'ownership_holding_pct',
            'ownership_sell_count', 'ownership_sell_share',
            'ownership_held_count', 'ownership_held_share',
            'ownership_buy_count', 'ownership_buy_share',
            'ownership_na', 'ownership_na_pct',
            'ownership_new_count', 'ownership_new_share',
            'ownership_out_count', 'ownership_out_share',
            'ownership_top15_sum', 'ownership_top15_na_pct',
        ]
        
        for key in keys:
            print key, getattr(self.enter_opinion, key)

            self.assertIsNotNone(getattr(self.enter_opinion, key))

        self.enter_opinion.ownership = True
        self.enter_opinion.save()

    def test_get_insider(self):
        """
        Test get ownership data from nasdaq html file
        """
        self.skipTest('Test only when need')
        self.enter_opinion.get_insider()

        keys = [
            'insider',
            'insider_buy_3m', 'insider_buy_12m',
            'insider_sell_3m', 'insider_sell_12m',
            'insider_buy_share_3m', 'insider_buy_share_12m',
            'insider_sell_share_3m', 'insider_sell_share_12m',
            'insider_na_3m', 'insider_na_12m',
        ]

        for key in keys:
            print key, getattr(self.enter_opinion, key)

        self.enter_opinion.insider = True
        self.enter_opinion.save()

    def test_get_short_interest(self):
        """
        Test get ownership data from nasdaq html file
        """
        self.skipTest('Test only when need')
        self.enter_opinion.get_short_interest()

        keys = [
            'short_interest', 'df_short_interest', 'short_squeeze'
        ]

        for key in keys:
            print key, getattr(self.enter_opinion, key)

        self.enter_opinion.short_interest = True
        self.enter_opinion.save()

    def test_get_rating(self):
        """
        Test get ownership data from nasdaq html file
        """
        self.skipTest('Test only when need')
        self.enter_opinion.get_rating()

        keys = [
            'analyst_rating', 'abr_current', 'abr_previous', 'abr_target', 'abr_rating_count'
        ]

        for key in keys:
            print key, getattr(self.enter_opinion, key)

        self.enter_opinion.analyst_rating = True
        self.assertTrue(self.enter_opinion.id)

    def test_enter_opinion_report(self):
        """
        Test enter opinion report
        :return:
        """
        self.market_opinion = MarketOpinion(**{
            'date': '2015-08-12',
            'short_trend0': 'BEAR',
            'short_trend1': 'BULL',
            'long_trend0': 'BEAR',
            'long_trend1': 'BULL',
            'short_persist': False,
            'long_persist': True,
            'description': '',
            'volatility': 'NORMAL',
            'bond': 'BEAR',
            'commodity': 'BEAR',
            'currency': 'RANGE',
            'market_indicator': 4,
            'extra_attention': 2,
            'key_indicator': 1,
            'special_news': False,
            'commentary': ''
        })
        self.market_opinion.save()

        self.statement = Statement(**{
            'date': '2015-08-12',
            'net_liquid': 25000.0,
            'stock_bp': 14900.0,
            'option_bp': 10100.0,
            'commission_ytd': 1850.0,
            'csv_data': ''
        })
        self.statement.save()

        response = self.client.get(
            reverse('admin:enter_opinion_report', kwargs={'id': self.enter_opinion.id})
        )

        print response




























