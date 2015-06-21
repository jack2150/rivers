from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from quant.models import Algorithm


class TestReadyAlgorithm(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.algorithm = Algorithm(
            rule='EWMA change of direction',
            formula='EMA = EMA(t)(k-1) - EMA(t-1)(k-1)',
            date='2015-06-19',
            category='technical',
            method='ewma',
            fname='cd.py',
            description='',
        )
        self.algorithm.save()

    def test_view(self):
        """
        Test ready algorithm form before start testing
        """
        response = self.client.get(reverse('admin:algorithm_analysis', args=(1, )))

        form = response.context['form']

        for key in form.initial.keys():
            print key, form.initial[key]

        self.assertTrue(form.initial['algorithm_id'])
        self.assertEqual(form.initial['algorithm_rule'],
                         'EWMA change of direction')
        self.assertTrue(form.initial['algorithm_formula'],
                        'EMA = EMA(t)(k-1) - EMA(t-1)(k-1)')

        # arguments exists
        print 'arguments that use for testing...'
        for key in ('span', 'previous'):
            print key, form[key]
            self.assertTrue(form[key])







