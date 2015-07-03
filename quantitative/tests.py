from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from quantitative.quant import AlgorithmQuant
from quantitative.models import Algorithm


class TestAlgorithm(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.algorithm = Algorithm(
            rule='EWMA change of direction - H',
            formula='EMA = EMA(t)(k-1) - EMA(t-1)(k-1)',
            date='2015-06-19',
            category='technical',
            method='ewma',
            path='technical.ewma.cd.cdh',
            description='',
        )
        self.algorithm.save()

    def test_make_quant(self):
        """
        Test make quant instance using algorithm methods
        """
        quant = self.algorithm.make_quant()
        print quant

        self.assertEqual(type(quant), AlgorithmQuant)

        self.assertTrue(quant.handle_data)
        self.assertTrue(quant.handle_data)

    def test_get_args(self):
        """
        Test get arguments from handle_data and create_signal
        """
        args = self.algorithm.get_args()
        print args

        self.assertEqual(args[0], ['span', 'previous'])
        self.assertEqual(args[1], ['holding'])


class TestAlgorithmAnalysis(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.algorithm = Algorithm(
            id=1,
            rule='EWMA change of direction',
            formula='EMA = EMA(t)(k-1) - EMA(t-1)(k-1)',
            date='2015-06-19',
            category='technical',
            method='ewma',
            path='technical.ewma.cd.cd',
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
        for key in ('handle_data_span', 'handle_data_previous'):
            print key, form[key]
            self.assertTrue(form[key])







