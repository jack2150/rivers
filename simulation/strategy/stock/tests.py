from base.utests import TestUnitSetUp
from quantitative.quant import AlgorithmQuant
from quantitative.models import Algorithm
import pandas as pd
from simulation.strategy.stock.stop_loss import create_order


class TestStockLimit(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'

        self.algorithm = Algorithm.objects.get(id=1)

        self.quant = self.algorithm.make_quant()
        self.quant.seed_data(self.symbol)

        self.arguments = {
            'span': 20,
            'previous': 20
        }

    def test_order(self):
        """
        Test trade using stop loss order
        """
        df_stock = self.quant.handle_data(self.quant.data[self.symbol], **self.arguments)
        df_signal = self.quant.create_signal(df_stock)
        r0 = pd.Series(self.quant.report(df_stock, df_signal))

        print 'using gtc stop loss order...'
        df_stop_loss = create_order(df_stock, df_signal, 'gtc', 10)

        # print df_stop_loss.to_string(line_width=200)
        r1 = pd.Series(self.quant.report(df_stock, df_stop_loss))

        print 'using close only stop loss order...'
        df_stop_loss = create_order(df_stock, df_signal, 'close', 5)

        # print df_stop_loss.to_string(line_width=200)
        r2 = pd.Series(self.quant.report(df_stock, df_stop_loss))

        print pd.DataFrame([r0, r1, r2]).to_string(line_width=300)
