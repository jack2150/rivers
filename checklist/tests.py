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
            'risk_profile': 'Moderate',
            'bp_effect': 2000.0,
            'reward': 2000.0,
            'risk': 3500.0,
            'size': 10,
            'enter_date': '2015-08-13',
            'exit_date': '2015-09-19',
            'signal': 'RANGE',
            'significant': True,
            'confirm': True,
            'target': 57.5,
            'description': '',
            'earning': 1,
            'dividend': 0,
            'split': 0,
            'special': 0,
            'news_level': 'WEAK',
            'news_signal': 'UNKNOWN',
            'chart0': 'BULL',
            'chart1': 'RANGE',
            'chart_persist': 1,
        })
        self.enter_opinion.save()
        self.assertTrue(self.enter_opinion.id)

    def test_get_ownership(self):
        """
        Test get ownership data from nasdaq html file
        """
        self.enter_opinion.get_ownership()
        
        keys = [
            'holding_pct', 'decrease_holder', 'decrease_shares',
            'held_holder', 'held_shares', 'increase_holder', 'increase_shares', 'net_activity',
            'net_activity_pct', 'new_holder', 'out_holder', 'new_shares', 'out_shares',
            'top15_activity', 'top15_holding'
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
        self.enter_opinion.get_insider()

        keys = [
            'symbol', 'date',
            'buy_trade_3m', 'buy_trade_12m', 'sell_trade_3m', 'sell_trade_12m',
            'buy_shares_3m', 'buy_shares_12m', 'sell_shares_3m', 'sell_shares_12m',
            'net_activity_3m', 'net_activity_12m'
        ]

        for key in keys:
            print key, getattr(self.enter_opinion, key)

        self.enter_opinion.insider = True
        self.enter_opinion.save()

    def test_get_short_interest(self):
        """
        Test get ownership data from nasdaq html file
        """
        self.enter_opinion.get_short_interest()

        print self.enter_opinion.df_short_interest

        self.enter_opinion.short_interest = True
        self.enter_opinion.save()

    def test_get_rating(self):
        """
        Test get ownership data from nasdaq html file
        """
        self.enter_opinion.get_rating()

        keys = [
            'current_abr', 'last_abr', 'no_recs', 'avg_target'
        ]

        for key in keys:
            print key, getattr(self.enter_opinion, key)

        self.enter_opinion.analyst_rating = True
        self.assertTrue(self.enter_opinion.id)


class TestEnterOpinionGenerateScore(TestSetUp):
    fixtures = ('wfc_score.json', )
    multi_db = True

    def setUp(self):
        TestSetUp.setUp(self)

        self.enter_opinion = EnterOpinion.objects.get(id=1)

    def test_generate_score(self):
        """

        :return:
        """
        self.enter_opinion.generate_score()


class TestEnterOpinionReport(TestSetUp):
    fixtures = ('wfc_score.json', )
    multi_db = True

    def setUp(self):
        TestSetUp.setUp(self)

        self.enter_opinion = EnterOpinion.objects.get(id=1)
        self.statement = Statement()
        self.statement.date = '2015-08-14'
        self.statement.net_liquid = 25000.0
        self.statement.stock_bp = 25000.0
        self.statement.option_bp = 25000.0
        self.statement.commission_ytd = 25000.0
        self.statement.save()

    def test_generate_score(self):
        """

        :return:
        """
        self.client.get(
            reverse('admin:enter_opinion_report', kwargs={'id': self.enter_opinion.id})
        )




























