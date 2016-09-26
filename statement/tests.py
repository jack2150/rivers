import os
from decimal import Decimal
from datetime import datetime
from glob import glob
from pprint import pprint
from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from rivers.settings import STATEMENT_DIR
from statement.models import *
import pandas as pd


class TestStatementModels(TestSetUp):
    def test_statement(self, output=True):
        lines = [
            'Net Liquidating Value, "$49,141.69"',
            'Stock Buying Power, "$36,435.34"',
            'Option Buying Power, "$36,435.34"',
            'Commissions / Fees YTD,$159.08',
        ]

        self.statement = Statement()
        self.statement.date = '2015-01-29'
        self.statement.load_csv(lines)
        self.statement.save()
        self.statement = Statement.objects.first()

        self.assertTrue(self.statement.id)
        self.assertEqual(self.statement.net_liquid, Decimal('49141.69'))
        self.assertEqual(self.statement.stock_bp, Decimal('36435.34'))
        self.assertEqual(self.statement.option_bp, Decimal('36435.34'))
        self.assertEqual(self.statement.commission_ytd, Decimal('159.08'))

        if output:
            df_statement = self.statement.to_hdf()
            print df_statement

    def test_cash_balance(self):
        self.test_statement(output=False)

        line = '1/29/15,14:39:44,TRD,472253620,BOT +100 RSX @14.93,,-9.99,"-1,493.00","48,429.44"'

        self.cash_balance = CashBalance()
        self.cash_balance.statement = self.statement
        self.cash_balance.load_csv(line)
        self.cash_balance.save()
        self.cash_balance = CashBalance.objects.get(id=self.cash_balance.id)

        self.assertTrue(self.cash_balance.id)
        self.assertEqual(self.cash_balance.time,
                         datetime.strptime('14:39:44', '%H:%M:%S').time())
        self.assertEqual(self.cash_balance.name, 'TRD')
        self.assertEqual(self.cash_balance.ref_no, 472253620)
        self.assertEqual(self.cash_balance.description, 'BOT +100 RSX @14.93')
        self.assertEqual(self.cash_balance.fee, Decimal('0.0'))
        self.assertEqual(self.cash_balance.commission, Decimal('-9.99'))
        self.assertEqual(self.cash_balance.amount, Decimal('-1493.00'))
        self.assertEqual(self.cash_balance.balance, Decimal('48429.44'))

        df = self.cash_balance.to_hdf()

        lines = [
            '1/29/15,01:00:00,BAL,,Cash balance at the start of business day 29.01 CST,,,,"50,000.00"',
            '1/29/15,14:35:49,LIQ,472251902,Cash liquidation,,,"75,000.00","125,000.00"',
            '1/29/15,14:40:29,TRD,472253683,BOT +200 RSX @14.92,,-9.99,"-2,984.00","41,759.46"',
            '1/29/15,14:41:40,TRD,472252394,SOLD -3 VERTICAL SPY 100 MAR 15 201/199 PUT @.75,'
            '-0.07,-14.49,225.00,"41,969.90"',
            '1/29/15,16:01:12,ADJ,,/QMH5 mark to market at 44.53 official settlement price,,,10.00,"50,572.71"',
        ]

        for line in lines:
            self.cash_balance = CashBalance()
            self.cash_balance.statement = self.statement
            self.cash_balance.load_csv(line)
            self.cash_balance.save()
            self.cash_balance = CashBalance.objects.get(id=self.cash_balance.id)

            df = df.append(self.cash_balance.to_hdf())

        print df.to_string(line_width=200)

    def test_account_order(self):
        self.test_statement(output=False)

        line = ',,1/29/15 14:42:59,COVERED,SELL,-1,TO OPEN,PG,MAR 15,87.5,CALL,84.70,LMT,DAY,FILLED'

        self.account_order = AccountOrder()
        self.account_order.statement = self.statement
        self.account_order.load_csv(line)
        self.account_order.save()
        self.account_order = AccountOrder.objects.get(id=self.account_order.id)

        self.assertTrue(self.account_order.id)
        self.assertEqual(self.account_order.time,
                         datetime.strptime('14:42:59', '%H:%M:%S').time())
        self.assertEqual(self.account_order.spread, 'COVERED')
        self.assertEqual(self.account_order.side, 'SELL')
        self.assertEqual(self.account_order.qty, '-1')
        self.assertEqual(self.account_order.pos_effect, 'TO OPEN')
        self.assertEqual(self.account_order.symbol, 'PG')
        self.assertEqual(self.account_order.exp, 'MAR 15')
        self.assertEqual(self.account_order.strike, Decimal('87.5'))
        self.assertEqual(self.account_order.contract, 'CALL')
        self.assertEqual(self.account_order.price, '84.70')
        self.assertEqual(self.account_order.order, 'LMT')
        self.assertEqual(self.account_order.tif, 'DAY')
        self.assertEqual(self.account_order.status, 'FILLED')

        df = self.account_order.to_hdf()

        lines = [
            ',,1/29/15 14:50:15,STOCK,SELL,-100,TO OPEN,KO,,,STOCK,42.20,LMT,DAY,EXPIRED',
            ',,1/29/15 14:41:12,VERTICAL,SELL,-2,TO OPEN,JPM,MAR 15,55,PUT,.70,LMT,DAY,FILLED',
            ',,1/29/15 14:41:12,VERTICAL,BUY,+2,TO OPEN,JPM,MAR 15,52.5,PUT,.70,LMT,DAY,FILLED',
            ',,1/29/15 14:40:29,STOCK,BUY,+200,TO OPEN,RSX,,,ETF,14.92,LMT,DAY,FILLED',
            ',,1/29/15 14:44:47,COVERED,SELL,-1,TO OPEN,SNDK,MAR 15,75,PUT,79.68,LMT,DAY,FILLED',
            ',,1/29/15 14:44:47,COVERED,SELL,-100,TO OPEN,SNDK,,,STOCK,79.6,LMT,DAY,FILLED',
            ',,1/29/15 14:42:25,STOCK,SELL,-100,TO OPEN,KO,,,STOCK,42.04,LMT,DAY,CANCELED'
        ]

        for line in lines:
            self.account_order = AccountOrder()
            self.account_order.statement = self.statement
            self.account_order.load_csv(line)
            self.account_order.save()
            self.account_order = AccountOrder.objects.get(id=self.account_order.id)

            df = df.append(self.account_order.to_hdf())

        print df.to_string(line_width=200)

    def test_account_trade(self):
        self.test_statement(output=False)

        line = ',1/29/15 14:41:40,VERTICAL,SELL,-3,TO OPEN,SPY,MAR 15,201,PUT,5.18,.75,LMT'

        self.account_trade = AccountTrade()
        self.account_trade.statement = self.statement
        self.account_trade.load_csv(line)
        self.account_trade.save()
        self.account_trade = AccountTrade.objects.get(id=self.account_trade.id)

        df = self.account_trade.to_hdf()

        self.assertTrue(self.account_trade.id)
        self.assertEqual(self.account_trade.time,
                         datetime.strptime('14:41:40', '%H:%M:%S').time())
        self.assertEqual(self.account_trade.spread, 'VERTICAL')
        self.assertEqual(self.account_trade.side, 'SELL')
        self.assertEqual(self.account_trade.qty, -3)
        self.assertEqual(self.account_trade.pos_effect, 'TO OPEN')
        self.assertEqual(self.account_trade.symbol, 'SPY')
        self.assertEqual(self.account_trade.exp, 'MAR 15')
        self.assertEqual(self.account_trade.strike, Decimal('201'))
        self.assertEqual(self.account_trade.contract, 'PUT')
        self.assertEqual(self.account_trade.price, Decimal('5.18'))
        self.assertEqual(self.account_trade.net_price, Decimal('.75'))
        self.assertEqual(self.account_trade.order_type, 'LMT')

        lines = [
            ',1/29/15 14:41:41,VERTICAL,BUY,+1,TO OPEN,TSLA,MAR 15,205,CALL,13.95,2.40,LMT',
            ',1/29/15 14:41:41,VERTICAL,SELL,-1,TO OPEN,TSLA,MAR 15,210,CALL,11.55,2.40,LMT',
            ',1/29/15 14:41:40,VERTICAL,SELL,-3,TO OPEN,SPY,MAR 15,201,PUT,5.18,-.75,LMT',
            ',1/29/15 14:41:40,VERTICAL,BUY,+3,TO OPEN,SPY,MAR 15,199,PUT,4.43,-.75,LMT',
            ',1/29/15 14:40:29,STOCK,BUY,+200,TO OPEN,RSX,,,ETF,14.92,14.92,LMT',
            ',1/29/15 14:40:07,STOCK,BUY,+200,TO OPEN,EWU,,,ETF,18.33,18.33,LMT',
        ]

        for line in lines:
            self.account_trade = AccountTrade()
            self.account_trade.statement = self.statement
            self.account_trade.load_csv(line)
            self.account_trade.save()
            self.account_trade = AccountTrade.objects.get(id=self.account_trade.id)

            df = df.append(self.account_trade.to_hdf())

        print df.to_string(line_width=200)

    def test_holding_equity(self):
        self.test_statement(output=False)

        line = 'EWU,ISHARES TRUST MSCI UNITED KINGDOM ETF,+200,18.33,18.37,"$3,674.00"'

        self.holding_equity = HoldingEquity()
        self.holding_equity.statement = self.statement
        self.holding_equity.load_csv(line)
        self.holding_equity.save()
        self.holding_equity = HoldingEquity.objects.get(id=self.holding_equity.id)

        self.assertTrue(self.holding_equity.id)
        self.assertEqual(self.holding_equity.symbol, 'EWU')
        self.assertEqual(self.holding_equity.description, 'ISHARES TRUST MSCI UNITED KINGDOM ETF')
        self.assertEqual(self.holding_equity.qty, 200)
        self.assertEqual(self.holding_equity.trade_price, Decimal('18.33'))
        self.assertEqual(self.holding_equity.close_price, Decimal('18.37'))
        self.assertEqual(self.holding_equity.close_value, Decimal('3674.00'))

        df = self.holding_equity.to_hdf()

        lines = [
            'XOM,EXXON MOBIL CORPORATION COM,-100,87.05,87.58,"($8,758.00)"',
            'EWU,ISHARES TRUST MSCI UNITED KINGDOM ETF,+200,18.33,18.37,"$3,674.00"',
            'RSX,MARKET VECTORS RUSSIA,+300,14.9233333,14.81,"$4,443.00"',
            'PG,PROCTER GAMBLE CO COM,+100,85.74,85.67,"$8,567.00"',
            'SNDK,SANDISK CORP COM,-100,76.95,77.47,"($7,747.00)"',
        ]

        for line in lines:
            self.holding_equity = HoldingEquity()
            self.holding_equity.statement = self.statement
            self.holding_equity.load_csv(line)
            self.holding_equity.save()
            self.holding_equity = HoldingEquity.objects.get(id=self.holding_equity.id)

            df = df.append(self.holding_equity.to_hdf())

        print df.to_string(line_width=200)

    def test_holding_option(self):
        self.test_statement(output=False)

        line = 'JPM,JPM150320P55,MAR 15,55,PUT,-2,1.46,1.4900973,($298.02)'

        self.holding_option = HoldingOption()
        self.holding_option.statement = self.statement
        self.holding_option.load_csv(line)
        self.holding_option.save()
        self.holding_option = HoldingOption.objects.get(id=self.holding_option.id)

        self.assertTrue(self.holding_option.id)
        self.assertEqual(self.holding_option.symbol, 'JPM')
        self.assertEqual(self.holding_option.option_code, 'JPM150320P55')
        self.assertEqual(self.holding_option.exp, 'MAR 15')
        self.assertEqual(self.holding_option.strike, Decimal('55'))
        self.assertEqual(self.holding_option.contract, 'PUT')
        self.assertEqual(self.holding_option.qty, -2)
        self.assertEqual(self.holding_option.trade_price, Decimal('1.46'))
        self.assertEqual(self.holding_option.close_price, Decimal('1.49'))
        self.assertEqual(self.holding_option.close_value, Decimal('-298.02'))

        df = self.holding_option.to_hdf()

        lines = [
            'WFC,WFC150320P50,MAR 15,50,PUT,+2,.68,.64,$128.00',
            'WFC,WFC150320P52.5,MAR 15,52.5,PUT,-2,1.48,1.40,($280.00)',
            'SPY,SPY150320P201,MAR 15,201,PUT,-3,5.18,4.62,"($1,386.00)"',
            'EBAY,EBAY150320C57.5,MAR 15,57.5,CALL,+2,.53,.515,$103.00',
            'JPM,JPM150320P52.5,MAR 15,52.5,PUT,+2,.76,.77,$154.00',
        ]

        for line in lines:
            self.holding_option = HoldingOption()
            self.holding_option.statement = self.statement
            self.holding_option.load_csv(line)
            self.holding_option.save()
            self.holding_option = HoldingOption.objects.get(id=self.holding_option.id)

            df = df.append(self.holding_option.to_hdf())

        print df.to_string(line_width=200)

    def test_profit_loss(self):
        self.test_statement(output=False)

        line = 'XOM,EXXON MOBIL CORPORATION COM,($28.00),-0.31%,' \
               '($28.00),($28.00),"$1,313.70","($8,995.00)"'

        self.profit_loss = ProfitLoss()
        self.profit_loss.statement = self.statement
        self.profit_loss.load_csv(line)
        self.profit_loss.save()
        self.profit_loss = ProfitLoss.objects.first()

        self.assertTrue(self.profit_loss.id)
        self.assertEqual(self.profit_loss.symbol, 'XOM')
        self.assertEqual(self.profit_loss.description, 'EXXON MOBIL CORPORATION COM')
        self.assertEqual(self.profit_loss.pl_open, Decimal('-28.0'))
        self.assertEqual(self.profit_loss.pl_pct, Decimal('-0.31'))
        self.assertEqual(self.profit_loss.pl_day, Decimal('-28.0'))
        self.assertEqual(self.profit_loss.pl_ytd, Decimal('-28.0'))
        self.assertEqual(self.profit_loss.margin_req, Decimal('1313.7'))
        self.assertEqual(self.profit_loss.close_value, Decimal('-8995.0'))

        df = self.profit_loss.to_hdf()

        self.assertTrue(self.profit_loss.id)

        lines = [
            'AAPL,APPLE INC COM,($2.50),-0.94%,($2.50),($2.50),$0.00,($267.50)',
            'EBAY,EBAY INC COM,$9.00,+5.63%,$9.00,$9.00,$0.00,($151.00)',
            'EWU,ISHARES TRUST MSCI UNITED KINGDOM ETF,$8.00,+0.22%,$8.00,$8.00,$551.10,"$3,674.00"',
            'GLD,SPDR GOLD TR GOLD SHS ETF,($7.00),-2.27%,($7.00),($7.00),$0.00,$301.00',
            'JPM,JP MORGAN CHASE & CO COM,($4.02),-2.87%,($4.02),($4.02),$0.00,($144.02)',
        ]

        # batch save
        for line in lines:
            self.profit_loss = ProfitLoss()
            self.profit_loss.statement = self.statement
            self.profit_loss.load_csv(line)
            self.profit_loss.save()
            self.profit_loss = ProfitLoss.objects.get(id=self.profit_loss.id)

            df = df.append(self.profit_loss.to_hdf())

        print df.to_string(line_width=200)


class TestPosition(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)
        self.position = Position()

        self.statement = Statement()
        self.statement.date = '2015-01-29'
        self.statement.load_csv([
            'Net Liquidating Value, "$49,141.69"', 'Stock Buying Power, "$36,435.34"',
            'Option Buying Power, "$36,435.34"', 'Commissions / Fees YTD,$159.08',
        ])
        self.statement.save()

        self.account_trade = AccountTrade()
        self.account_trade.statement = self.statement
        self.account_trade.load_csv(
            ',1/29/15 14:40:29,STOCK,BUY,+200,TO OPEN,RSX,,,ETF,14.92,14.92,LMT'
        )
        self.account_trade.save()

    def test_set_open(self, output=True):
        """
        Test open a new position
        """
        self.position.set_open(trades=AccountTrade.objects.all())
        self.position.save()

        if output:
            print 'open position:', self.position

        self.assertTrue(self.position.id)
        self.assertEqual(self.position.status, 'OPEN')
        self.assertEqual(self.position.name, 'STOCK')
        self.assertEqual(self.position.spread, 'LONG_STOCK')

    def test_set_close(self):
        """
        Test close a existing position
        """
        self.test_set_open(output=False)

        self.position.set_close(date='2015-04-29')
        self.position.save()

        print 'position status:', self.position.status
        print 'position stop:', self.position.stop

        self.assertEqual(self.position.status, 'CLOSE')
        self.assertEqual(self.position.stop, '2015-04-29')

    def test_set_expire(self):
        """
        Test position set expire
        """
        self.test_set_open(output=False)
        self.position.set_expire(date='2015-04-29')

        print 'position status:', self.position.status

        self.assertEqual(self.position.status, 'EXPIRE')

    def test_set_custom(self):
        """
        Test position set custom
        """
        self.position.set_custom()

        print 'position name:', self.position.name
        print 'position spread:', self.position.spread

        self.assertEqual(self.position.name, 'CUSTOM')
        self.assertEqual(self.position.spread, 'CUSTOM')

    def test_conditions1(self):
        """
        Test create conditions from position stage
        """
        self.test_set_open(output=False)

        self.position.positionstage_set.add(PositionStage(
            price=100.0,
            gt_stage='PROFIT', gt_amount=0.0,
            e_stage='EVEN', e_amount=0.0,
            lt_stage='LOSS', lt_amount=0.0,
        ))

        print 'run make conditions...'
        conditions = self.position.make_conditions()
        print 'condition list:'
        pprint(conditions)

        self.assertTrue(eval(conditions[0][1].format(x=90)))
        self.assertTrue(eval(conditions[1][1].format(x=100)))
        self.assertTrue(eval(conditions[2][1].format(x=110)))

        self.assertEqual(len(conditions), 3)

        # test current stage
        self.assertEqual(self.position.current_stage(price=99), 'LOSS')
        self.assertEqual(self.position.current_stage(price=100), 'EVEN')
        self.assertEqual(self.position.current_stage(price=101), 'PROFIT')

    def test_conditions2(self):
        self.test_set_open(output=False)
        self.position.positionstage_set.add(PositionStage(
            price=110.0,
            gt_stage='MAX_PROFIT', gt_amount=250,
            e_stage='MAX_PROFIT', e_amount=250,
            lt_stage='PROFIT', lt_amount=250
        ))

        self.position.positionstage_set.add(PositionStage(
            price=100.0,
            gt_stage='PROFIT', gt_amount=0.0,
            e_stage='EVEN', e_amount=0.0,
            lt_stage='LOSS', lt_amount=0.0
        ))

        self.position.positionstage_set.add(PositionStage(
            price=95.0,
            gt_stage='LOSS', gt_amount=-180,
            e_stage='MAX_LOSS', e_amount=-180,
            lt_stage='MAX_LOSS', lt_amount=-180
        ))

        print 'run make conditions...'

        conditions = self.position.make_conditions()
        print 'condition list:'
        pprint(conditions)

        self.assertTrue(eval(conditions[0][1].format(x=90)))
        self.assertTrue(eval(conditions[0][1].format(x=95)))
        self.assertTrue(eval(conditions[1][1].format(x=96)))
        self.assertTrue(eval(conditions[1][1].format(x=99)))
        self.assertTrue(eval(conditions[2][1].format(x=100)))
        self.assertTrue(eval(conditions[3][1].format(x=101)))
        self.assertTrue(eval(conditions[3][1].format(x=109)))
        self.assertTrue(eval(conditions[4][1].format(x=110)))
        self.assertTrue(eval(conditions[4][1].format(x=120)))

        self.assertEqual(len(conditions), 5)

        # test current stage
        """
        self.assertEqual(self.position.current_stage(price=90), 'MAX_LOSS')
        self.assertEqual(self.position.current_stage(price=95), 'MAX_LOSS')
        self.assertEqual(self.position.current_stage(price=96), 'LOSS')
        self.assertEqual(self.position.current_stage(price=99), 'LOSS')
        self.assertEqual(self.position.current_stage(price=100), 'EVEN')
        self.assertEqual(self.position.current_stage(price=101), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=109), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=110), 'MAX_PROFIT')
        self.assertEqual(self.position.current_stage(price=120), 'MAX_PROFIT')
        """

    def test_create_stages(self):
        """
        Test create stage using trades
        """
        self.position.set_open(trades=AccountTrade.objects.all())
        self.position.save()

        print 'run create_stages...'
        self.position.create_stages(trades=AccountTrade.objects.all())

        self.assertTrue(self.position.positionstage_set.exists())

        for stage in self.position.positionstage_set.all():
            print stage


class TestPositionStage(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.position = Position()
        self.position.name = 'STOCK'
        self.position.spread = 'LONG_STOCK'
        self.position.start = '2015-04-29'
        self.position.save()

        self.stage = PositionStage()
        self.stage.position = self.position

    def test_stage(self, output=True):
        """
        Test create stage
        """
        self.stage.price = 29.6

        self.stage.gt_stage = 'PROFIT'
        self.stage.e_stage = 'EVEN'
        self.stage.lt_stage = 'LOSS'
        self.stage.save()

        self.assertTrue(self.stage.id)
        self.assertEqual(self.stage.gt_stage, 'PROFIT')
        self.assertFalse(self.stage.gt_amount)
        self.assertEqual(self.stage.e_stage, 'EVEN')
        self.assertFalse(self.stage.e_amount)
        self.assertEqual(self.stage.lt_stage, 'LOSS')
        self.assertFalse(self.stage.lt_amount)

        if output:
            print self.stage.to_hdf()

    def test_check(self):
        """
        Test check price for stage
        """
        self.test_stage(output=False)

        prices = [30, 29.6, 29]
        expects = ['PROFIT', 'EVEN', 'LOSS']

        for price, expect in zip(prices, expects):
            result = self.stage.check_status(price)
            self.assertEqual(result, expect)
            print 'price: %.2f, result: %s' % (price, result)


class TestStatementImport(TestSetUp):
    def test_statement_import(self):
        print 'run client get statement import view...'
        response = self.client.get(reverse('admin:statement_import'))

        title = response.context['title']
        files = response.context['files']

        self.assertEqual(title, 'Statement Import')
        self.assertGreater(len(files), 1)

        print 'statement:', Statement.objects.count()
        print 'account order:', AccountOrder.objects.count()
        print 'account trade:', AccountTrade.objects.count()
        print 'holding equity:', HoldingEquity.objects.count()
        print 'holding option:', HoldingOption.objects.count()
        print 'profit loss:', ProfitLoss.objects.count()

        self.assertTrue(Statement.objects.count())
        self.assertTrue(AccountOrder.objects.count())
        self.assertTrue(AccountTrade.objects.count())
        self.assertTrue(HoldingEquity.objects.count())
        self.assertTrue(HoldingOption.objects.count())
        self.assertTrue(ProfitLoss.objects.count())


class TestStatementController(TestSetUp):
    fixtures = ('no_pos.json', )

    def setUp(self):
        TestSetUp.setUp(self)

        self.statement = Statement.objects.order_by('date').first()

    def test_position_trades(self):
        """
        Test using account trade to open and close position
        """
        Position.objects.all().delete()
        for statement in Statement.objects.all():
            statement.controller.add_relations()
            statement.controller.position_trades()
            statement.controller.position_expires()

        for position in Position.objects.all():
            print position
            print position.accounttrade_set.all()

            print 'cash balance:', position.cashbalance_set.count(),
            print 'account order:', position.accountorder_set.count(),
            print 'account trade:', position.accounttrade_set.count(),
            print 'holding equity:', position.holdingequity_set.count(),
            print 'holding option:', position.holdingoption_set.count(),
            print 'profit loss:', position.profitloss_set.count(), '\n'

            self.assertGreater(position.cashbalance_set.count(), 0)
            self.assertGreater(position.accountorder_set.count(), 0)
            self.assertGreater(position.accounttrade_set.count(), 0)
            if position.start != position.stop:  # day trade maybe no pl because multi positions
                self.assertTrue(position.holdingequity_set.exists() or position.holdingoption_set.exists())
                self.assertGreater(position.profitloss_set.count(), 0)

        print '\n\n' + '.' * 100 + '\n\n'

        print 'total position:', Position.objects.count()
        print 'total open position:', Position.objects.filter(status='OPEN').count()
        print 'total close position:', Position.objects.filter(status='CLOSE').count()
        print 'total expire position:', Position.objects.filter(status='EXPIRE').count()


class TestRealMoneyStatement(TestSetUp):
    def test_check_statement_files(self):
        """
        Check all statement date files is exists
        """
        files = glob(os.path.join(STATEMENT_DIR, 'real0', '*.csv'))

        dates0 = []
        for f in files:
            fname = os.path.basename(f)
            date = datetime.strptime(fname[:10], '%Y-%m-%d')
            # print date, , date.strftime('%a')

            if date.weekday() not in (5, 6):
                dates0.append(date)

        dates1 = list(pd.bdate_range(start=dates0[0], end=dates0[-1]))
        print len(dates0), len(dates1)

        for f in dates1:
            if f not in dates0:
                print f.strftime('%m/%d/%Y'), 'not found'
