from importlib import import_module
from django.db import models
from django.db.models import Q
from pandas import DataFrame
from base.ufunc import remove_comma


class Statement(models.Model):
    """
    Account Summary
    Net Liquidating Value,"$49,141.69"
    Stock Buying Power,"$36,435.34"
    Option Buying Power,"$36,435.34"
    Commissions/Fees YTD,$159.08
    Futures Commissions YTD,$0.00 <-- skip futures
    """
    date = models.DateField(unique=True)

    net_liquid = models.DecimalField(max_digits=20, decimal_places=2)
    stock_bp = models.DecimalField(max_digits=20, decimal_places=2)
    option_bp = models.DecimalField(max_digits=20, decimal_places=2)
    commission_ytd = models.DecimalField(max_digits=20, decimal_places=2)

    csv_data = models.TextField(blank=True)

    def load_csv(self, lines):
        """
        Input csv last 5 lines, format then save statement
        :param lines: str
        :return: Statement
        """
        values = list()
        for line in [x.replace('$', '') for x in lines]:
            if '"' in line:
                values.append(map(lambda y: y.replace(',', ''), line.split('"')[1::2])[0])
            else:
                values.append(line.split(',')[1])

        self.net_liquid = values[0] if values[0] != 'N/A' else 0.0
        self.stock_bp = values[1] if values[1] != 'N/A' else 0.0
        self.option_bp = values[2] if values[2] != 'N/A' else 0.0
        self.commission_ytd = values[3]

        return self

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.net_liquid, self.stock_bp, self.option_bp, self.commission_ytd]],
            index=[self.date],
            columns=['Net Liquid', 'Stock BP', 'Option BP', 'Commission YTD']
        )

    def __unicode__(self):
        return 'Statement {date}'.format(
            date=self.date
        )

    class Controller(object):
        def __init__(self, statement):
            self.statement = statement
            self.account_trades = self.statement.accounttrade_set

            self.open_positions = Position.objects.filter(status='OPEN')
            """:type: QuerySet"""

        def position_trades(self):
            """
            Loop trade by trade and open or close position
            :return: None
            """
            times = sorted(set([x[0] for x in self.account_trades.values_list('time')]))

            for time in times:
                for symbol in set([t.symbol for t in self.account_trades.filter(time=time)]):
                #for symbol in set([t.symbol for t in self.account_trades.filter(time=time) if t.symbol=='XOM']):
                    trades = self.account_trades.filter(Q(time=time) & Q(symbol=symbol)).order_by('time')
                    """:type: QuerySet"""

                    if len(list(set([t.pos_effect for t in trades]))) > 1:
                        raise ValueError('Difference pos effect for account trades.')
                    pos_effect = trades[0].pos_effect

                    if pos_effect == 'TO OPEN':
                        if self.open_positions.filter(symbol=symbol).exists():
                            position = self.open_positions.get(symbol=symbol)

                            # if strategy not same
                            if position.spread != Position().set_open(trades).spread:
                                position.set_custom()
                                position.save()
                        else:
                            position = Position()
                            position.set_open(trades)
                            position.save()
                            position.create_stages(trades)
                            self.add_relations(symbol=symbol, time=time)
                    elif pos_effect == 'TO CLOSE':
                        if self.open_positions.filter(symbol=symbol).exists():
                            self.add_relations(symbol=symbol, time=time)
                            position = self.open_positions.get(symbol=symbol)
                            position.set_close(self.statement.date)
                            position.save()
                        else:
                            #print trades[0].statement.date, trades
                            raise ValueError('Position <{symbol}> not found when closing.'.format(
                                symbol=symbol
                            ))
                    else:
                        raise ValueError('Wrong pos effect when open or close position.')

                    # add relation here
                    for trade in trades:
                        position.accounttrade_set.add(trade)

        def position_expires(self):
            """
            Set expire position
            :return: None
            """
            for position in Position.objects.filter(status='OPEN'):
                equity = self.statement.holdingequity_set.filter(symbol=position.symbol)
                option = self.statement.holdingoption_set.filter(symbol=position.symbol)

                if not(equity.exists() or option.exists()):
                    position.set_expire(self.statement.date)
                    position.save()

        def add_relations(self, symbol=None, time=None):
            """
            Set related objects (profit loss, equity, options)
            """
            if symbol:
                positions = [Position.objects.get(Q(symbol=symbol) & Q(status='OPEN'))]
            else:
                positions = self.open_positions

            for position in positions:
                f1 = (Q(symbol=position.symbol) & Q(position__isnull=True))
                f2 = f1 & (Q(time__lte=time) if time else
                           Q(time__in=position.accounttrade_set.all().values('time')))

                for account_order in self.statement.accountorder_set.filter(f2):
                    position.accountorder_set.add(account_order)

                for holding_equity in self.statement.holdingequity_set.filter(f1):
                    position.holdingequity_set.add(holding_equity)

                for holding_option in self.statement.holdingoption_set.filter(f1):
                    position.holdingoption_set.add(holding_option)

                for profit_loss in self.statement.profitloss_set.filter(f1):
                    position.profitloss_set.add(profit_loss)

                for cash_balance in self.statement.cashbalance_set.filter(position__isnull=True):
                    values = cash_balance.description.split(' ')[:5]
                    if position.symbol in values and time == cash_balance.time:
                        position.cashbalance_set.add(cash_balance)



    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)

        self.controller = Statement.Controller(self)


class Position(models.Model):
    symbol = models.CharField(max_length=20)

    name = models.CharField(max_length=100)
    spread = models.CharField(max_length=100)
    status = models.CharField(max_length=6, default='OPEN')

    start = models.DateField()
    stop = models.DateField(null=True, blank=True, default=None)

    def set_open(self, trades):
        """
        Open a new position
        :param trades: QuerySet
        :return: Position
        """
        self.status = 'OPEN'

        # set symbol
        self.symbol = trades[0].symbol

        # set start date
        self.start = trades[0].statement.date

        # set name
        spreads = list(set([trade.spread for trade in trades]))
        if len(spreads) > 1:
            raise ValueError('Different trade orders for single symbol in account statement.')

        if spreads in ('FUTURE', 'FOREX'):
            raise ValueError('Future or forex account trades.')
        else:
            self.name = spreads[0]  # for stock, single option or covered position

        # set spread
        self.spread = 'CUSTOM'
        if self.name == 'STOCK':
            self.spread = '{side}_STOCK'.format(
                side='LONG' if trades[0].qty > 0 else 'SHORT'
            )
        elif self.name == 'SINGLE':  # single option
            self.spread = '{side}_{contract}'.format(
                side='LONG' if trades[0].side == 'BUY' else 'NAKED',
                contract=trades[0].contract
            )
        elif self.name == 'COVERED':
            stock_order = trades.get(contract='STOCK')
            option_order = trades.get(Q(contract='CALL') | Q(contract='PUT'))

            if stock_order.side == 'BUY':
                if option_order.side == 'BUY' and option_order.contract == 'PUT':
                    self.spread = 'PROTECTIVE_PUT'
                elif option_order.side == 'SELL' and option_order.contract == 'CALL':
                    self.spread = 'COVERED_CALL'
            elif stock_order.side == 'SELL':
                if option_order.side == 'BUY' and option_order.contract == 'CALL':
                    self.spread = 'PROTECTIVE_CALL'
                elif option_order.side == 'SELL' and option_order.contract == 'PUT':
                    self.spread = 'COVERED_PUT'
        elif self.name == 'CUSTOM':
            self.spread = 'CUSTOM'
        else:
            self.spread = '{side}_{contract}{spread}'.format(
                side='LONG' if trades[0].net_price > 0 else 'SHORT',
                contract=(trades[0].contract + '_'
                          if len(list(set([t.contract for t in trades]))) == 1
                          else ''),
                spread=spreads[0]
            )

        return self

    def create_stages(self, trades):
        """
        Create stage using position trades
        :return:
        """
        if self.name and self.spread and self.name != 'CUSTOM':
            try:
                stage_module = import_module(
                    'statement.position.stages.{name}'.format(name=self.name.lower())
                )

                stage_cls = getattr(
                    stage_module,
                    'Stage{spread}'.format(
                        spread=''.join([x.lower().capitalize() for x in self.spread.split('_')])
                    )
                )

                stages = stage_cls(trades).create()
                for stage in stages:
                    self.positionstage_set.add(stage)

                #print self.spread, stages

            except (AttributeError, ImportError):
                pass
                #print '{name}.{spread} not yet implement.'.format(
                #    name=self.name, spread=self.spread
                #)
        else:
            raise ValueError('Please set name and spread before run create_stages.')

    def set_close(self, date):
        """
        Close current position
        :param date: DateTime
        :return: Position
        """
        if self.id:
            self.status = 'CLOSE'
            self.stop = date
        else:
            raise ValueError('Please close a existing positions.')

    def set_expire(self, date):
        """
        Set position expire
        :param date: DateTime
        :return: Position
        """
        if self.id:
            self.status = 'EXPIRE'
            self.stop = date
        else:
            raise ValueError('Please set expire a existing position')

        return self

    def set_custom(self):
        """
        Set position is custom
        :rtype : Position
        """
        self.name = 'CUSTOM'
        self.spread = 'CUSTOM'

        return self

    def make_conditions(self):
        """
        Get all stage and make condition
        :return: list of str
        """
        conditions = list()

        # make all stage into a list
        operators = list()
        for stage_list in self.positionstage_set.order_by('price').all():
            operators += [(stage_list.price, '<', stage_list.lt_stage, stage_list.lt_amount),
                          (stage_list.price, '==', stage_list.e_stage, stage_list.e_amount),
                          (stage_list.price, '>', stage_list.gt_stage, stage_list.gt_amount)]

        # make a list of same stage
        stages = list()
        last = 0
        for key, (s0, s1) in enumerate(zip(operators[:-1], operators[1:])):
            if s0[2] != s1[2]:
                stages.append(operators[last:key + 1])
                last = key + 1
        else:
            stages.append(operators[last:len(operators)])

        for stage_list in stages:
            condition0 = list()
            for price in sorted(set([s[0] for s in stage_list])):
                condition1 = list()
                for stage in [s for s in stage_list if s[0] == price]:
                    condition1.append('{x} {operator} {price}'.format(
                        x='{x}',
                        operator=stage[1],
                        price=stage[0],
                    ))
                condition0.append(' or '.join(condition1))

            conditions.append((stage_list[0][2], ' and '.join(condition0)))

        return conditions

    def current_stage(self, price):
        """
        Get current stage using price
        :param price: float
        :return: str
        """
        result = None
        for stage, condition in self.make_conditions():
            if eval(condition.format(x=price)):
                result = stage
                break

        return result

    def __unicode__(self):
        return '{symbol} {spread} {status} {date}'.format(
            symbol=self.symbol,
            spread=self.spread,
            status=self.status,
            date=self.stop if self.stop else self.start
        )


class PositionStage(models.Model):
    """
    A position price stage when current price reach a certain level
    """
    price = models.DecimalField(max_digits=10, decimal_places=2)

    gt_stage = models.CharField(max_length=20)
    gt_amount = models.DecimalField(null=True, max_digits=10, decimal_places=2)

    e_stage = models.CharField(max_length=20)
    e_amount = models.DecimalField(null=True, max_digits=10, decimal_places=2)

    lt_stage = models.CharField(max_length=20)
    lt_amount = models.CharField(null=True, max_length=20)

    position = models.ForeignKey(Position, null=True)

    def check(self, price):
        """
        """
        result = None
        for operator, status in (('>', 'gt_stage'), ('==', 'e_stage'), ('<', 'lt_stage')):
            formula = '{check_price} {operator} {stage_price}'.format(
                check_price=price,
                operator=operator,
                stage_price=self.price
            )

            if eval(formula):
                result = getattr(self, status)
                break

        return result

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.price, self.gt_stage, self.gt_amount, self.e_stage, self.e_amount,
                   self.lt_stage, self.lt_amount]],
            index=[self.id],
            columns=['Price', 'P>C', 'P>C $', 'P=C', 'P=C $', 'P<C', 'P<C $']
        )

    def __unicode__(self):
        format_amount = lambda x: ('' if x is None else (
            ' {:+.2f}'.format(float(x)) if x else ' 0.00'
        ))

        return 'p < {p} is {lts}{lta}, p == {p} is {es}{ea}, p > {p} is {gts}{gta}'.format(
            p=self.price,
            lts=self.lt_stage,
            lta=format_amount(self.lt_amount),
            es=self.e_stage,
            ea=format_amount(self.e_amount),
            gts=self.gt_stage,
            gta=format_amount(self.gt_amount),
        )


class CashBalance(models.Model):
    """
    DATE,TIME,TYPE,REF #,DESCRIPTION,FEES,COMMISSIONS,AMOUNT,BALANCE
    1/29/15,01:00:00,BAL,,Cash balance at the start of business day 29.01 CST,,,,"50,000.00"
    1/29/15,14:35:49,LIQ,472251902,Cash liquidation,,,"75,000.00","125,000.00"
    """
    time = models.TimeField()
    name = models.CharField(max_length=20)
    ref_no = models.BigIntegerField(null=True, blank=True)
    description = models.CharField(max_length=200, null=True, blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    commission = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2)

    statement = models.ForeignKey(Statement, null=True)
    position = models.ForeignKey(Position, null=True)

    def load_csv(self, line):
        """
        Format cash_balance csv line data, save it and return object
        :param line: str
        :return: CashBalance
        """
        line = remove_comma(line)

        values = map(
            lambda x: 0 if x == '' else x, line.split(',')
        )

        self.time = values[1]
        self.name = values[2]
        self.ref_no = values[3]
        self.description = values[4]
        self.fee = values[5]
        self.commission = values[6]
        self.amount = values[7]
        self.balance = values[8] if values[8] != 'N/A' else 0.0

        return self

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.time, self.name, self.ref_no, self.description,
                   self.fee, self.commission, self.amount, self.balance]],
            index=[self.statement.date],
            columns=['Time', 'Name', 'Ref #', 'Description', 'Fees',
                     'Commissions', 'Amount', 'Balance']
        )

    def __unicode__(self):
        return self.description


class AccountOrder(models.Model):
    """
    Notes,,Time Placed,Spread,Side,Qty,Pos Effect,Symbol,Exp,Strike,Type,PRICE,,TIF,Status
    ,,1/29/15 14:45:15,VERTICAL,SELL,-2,TO OPEN,EBAY,MAR 15,55,CALL,.73,LMT,DAY,CANCELED
    ,,,,BUY,+2,TO OPEN,EBAY,MAR 15,57.5,CALL,,,,
    """
    time = models.TimeField()
    spread = models.CharField(max_length=50)
    side = models.CharField(max_length=4)
    qty = models.CharField(max_length=100)
    pos_effect = models.CharField(max_length=50)
    symbol = models.CharField(max_length=20)
    exp = models.CharField(max_length=50, null=True, blank=True)
    strike = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    contract = models.CharField(max_length=10, null=True, blank=True)
    price = models.CharField(max_length=100)
    order = models.CharField(max_length=20)
    tif = models.CharField(max_length=20)
    status = models.CharField(max_length=500)

    statement = models.ForeignKey(Statement, null=True)
    position = models.ForeignKey(Position, null=True)

    def load_csv(self, line):
        """
        Format account_order csv line data, save it and return object
        :param line: str
        :return: HoldingEquity
        """
        line = remove_comma(line)
        values = line.split(',')

        self.time = values[2].split(' ')[1]
        self.spread = values[3]
        self.side = values[4]
        self.qty = values[5]
        self.pos_effect = values[6]
        self.symbol = values[7]
        self.exp = values[8] if values[8] else ''
        self.strike = values[9] if values[9] else 0.0
        self.contract = values[10]
        self.price = values[11] if values[11] else 0.0
        self.order = values[12]
        self.tif = values[13]
        self.status = values[14]

        return self

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.time, self.spread, self.side, self.qty, self.pos_effect,
                   self.symbol, self.exp, self.strike if self.strike else '',
                   self.contract, self.price, self.order, self.tif, self.status]],
            index=[self.statement.date],
            columns=['Time Placed', 'Spread', 'Side', 'Qty', 'Pos Effect', 'Symbol',
                     'Exp', 'Strike', 'Type', 'PRICE', 'Order', 'TIF', 'Status']
        )

    def __unicode__(self):
        return '{side} {qty} {symbol} {contract} {price} {order}'.format(
            side=self.side,
            qty=self.qty,
            symbol=self.symbol,
            contract=self.spread if self.spread == 'STOCK' else '{contract} {exp} {strike}'.format(
                contract=self.contract,
                exp=self.exp,
                strike=self.strike
            ),
            price=self.price,
            order=self.order
        )


class AccountTrade(models.Model):
    """
    ,Exec Time,Spread,Side,Qty,Pos Effect,Symbol,Exp,Strike,Type,Price,Net Price,Order Type
    ,1/29/15 15:43:06,VERTICAL,SELL,-2,TO OPEN,EBAY,MAR 15,55,CALL,1.33,.80,LMT
    ,,,BUY,+2,TO OPEN,EBAY,MAR 15,57.5,CALL,.53,CREDIT,
    """
    time = models.TimeField()
    spread = models.CharField(max_length=50)
    side = models.CharField(max_length=4)
    qty = models.IntegerField()
    pos_effect = models.CharField(max_length=50)
    symbol = models.CharField(max_length=20)
    exp = models.CharField(max_length=50, null=True, blank=True)
    strike = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    contract = models.CharField(max_length=10, null=True, blank=True)
    price = models.DecimalField(max_digits=20, decimal_places=2)
    net_price = models.DecimalField(max_digits=20, decimal_places=2)
    order_type = models.CharField(max_length=20)

    statement = models.ForeignKey(Statement, null=True)
    position = models.ForeignKey(Position, null=True)

    def load_csv(self, line):
        """
        Format account_trade csv line data, save it and return object
        :param line: str
        :return: HoldingEquity
        """
        line = remove_comma(line)
        values = line.split(',')

        self.time = values[1].split(' ')[1]
        self.spread = values[2]
        self.side = values[3]
        self.qty = values[4]
        self.pos_effect = values[5]
        self.symbol = values[6]
        self.exp = values[7]
        self.strike = values[8] if values[8] else 0
        self.contract = values[9]
        self.price = values[10]
        self.net_price = values[11]
        self.order_type = values[12]

        return self

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.time, self.spread, self.side, self.qty, self.pos_effect,
                   self.symbol, self.exp, self.strike if self.strike else '',
                   self.contract, self.price, self.net_price, self.order_type]],
            index=[self.statement.date],
            columns=['Exec Time', 'Spread', 'Side', 'Qty', 'Pos Effect', 'Symbol',
                     'Exp', 'Strike', 'Type', 'Price', 'Net Price', 'Order Type']
        )

    def __unicode__(self):
        return '{side} {qty} {symbol} {contract} {price} {pos_effect}'.format(
            side=self.side,
            qty=self.qty,
            symbol=self.symbol,
            contract=self.spread if self.spread == 'STOCK' else '{contract} {exp} {strike}'.format(
                contract=self.contract,
                exp=self.exp,
                strike=self.strike
            ),
            price=self.price,
            pos_effect=self.pos_effect
        )


class HoldingEquity(models.Model):
    """
    Symbol,Description,Qty,Trade Price,Close Price,Close Value
    XOM,EXXON MOBIL CORPORATION COM,-100,87.05,87.58,"($8,758.00)"
    """
    symbol = models.CharField(max_length=20)
    description = models.CharField(max_length=200)
    qty = models.IntegerField()
    trade_price = models.DecimalField(max_digits=20, decimal_places=2)
    close_price = models.DecimalField(max_digits=20, decimal_places=2)
    close_value = models.DecimalField(max_digits=20, decimal_places=2)

    statement = models.ForeignKey(Statement, null=True)
    position = models.ForeignKey(Position, null=True)

    def load_csv(self, line):
        """
        Format holding_equity csv line data, save it and return object
        :param line: str
        :return: HoldingEquity
        """
        line = remove_comma(line)

        values = [
            ('-' + x[1:-1] if x[0] == '(' and x[-1] == ')' else x)
            for x in [x.replace('$', '') for x in line.split(',')]
        ]

        self.symbol = values[0]
        self.description = values[1]
        self.qty = values[2]
        self.trade_price = values[3]
        self.close_price = values[4]
        self.close_value = values[5]

        return self

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.symbol, self.description, self.qty,
                   self.trade_price, self.close_price, self.close_value]],
            index=[self.statement.date],
            columns=['Symbol', 'Description', 'Qty', 'Trade Price',
                     'Close Price', 'Close Value']
        )

    def __unicode__(self):
        return '{qty} {symbol} {close_price}'.format(
            symbol=self.symbol,
            qty=self.qty,
            close_price=self.close_price
        )


class HoldingOption(models.Model):
    """
    Symbol,Option Code,Exp,Strike,Type,Qty,Trade Price,Close Price,Close Value
    TSLA,TSLA150320C205,MAR 15,205,CALL,+1,13.95,14.075,"$1,407.50"
    """
    symbol = models.CharField(max_length=20)
    option_code = models.CharField(max_length=200)
    exp = models.CharField(max_length=50)
    strike = models.DecimalField(max_digits=20, decimal_places=2)
    contract = models.CharField(max_length=10)
    qty = models.IntegerField()
    trade_price = models.DecimalField(max_digits=20, decimal_places=2)
    close_price = models.DecimalField(max_digits=20, decimal_places=2)
    close_value = models.DecimalField(max_digits=20, decimal_places=2)

    statement = models.ForeignKey(Statement, null=True)
    position = models.ForeignKey(Position, null=True)

    def load_csv(self, line):
        """
        Format holding_option csv line data, save it and return object
        :param line: str
        :return: HoldingEquity
        """
        line = remove_comma(line)

        values = [
            ('-' + x[1:-1] if x[0] == '(' and x[-1] == ')' else x)
            for x in [x.replace('$', '') for x in line.split(',')]
        ]

        self.symbol = values[0]
        self.option_code = values[1]
        self.exp = values[2]
        self.strike = values[3]
        self.contract = values[4]
        self.qty = values[5]
        self.trade_price = values[6]
        self.close_price = values[7]
        self.close_value = values[8]

        return self

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.symbol, self.option_code, self.exp, self.strike, self.contract,
                   self.qty, self.trade_price, self.close_price, self.close_value]],
            index=[self.statement.date],
            columns=['Symbol', 'Option Code', 'Exp', 'Strike', 'Type',
                     'Qty', 'Trade Price', 'Close Price', 'Close Value']
        )

    def __unicode__(self):
        return '{qty} {symbol} {exp} {strike} {contract}'.format(
            qty=self.qty,
            symbol=self.symbol,
            exp=self.exp,
            strike=self.strike,
            contract=self.contract
        )


class ProfitLoss(models.Model):
    """
    Symbol,Description,P/L Open,P/L %,P/L Day,P/L YTD,P/L Diff,Margin Req,Close Value
    XOM,EXXON MOBIL CORPORATION COM,($28.00),-0.31%,($28.00),($28.00),$0.00,"$1,313.70","($8,995.00)"
    """
    symbol = models.CharField(max_length=20)
    description = models.CharField(max_length=200)
    pl_open = models.DecimalField(max_digits=20, decimal_places=2)
    pl_pct = models.DecimalField(max_digits=20, decimal_places=2)
    pl_day = models.DecimalField(max_digits=20, decimal_places=2)
    pl_ytd = models.DecimalField(max_digits=20, decimal_places=2)
    margin_req = models.DecimalField(max_digits=20, decimal_places=2)
    close_value = models.DecimalField(max_digits=20, decimal_places=2)

    statement = models.ForeignKey(Statement, null=True)
    position = models.ForeignKey(Position, null=True)

    def load_csv(self, line):
        """
        Format profit_loss csv line data, save it and return object
        :param line: str
        :return: ProfitLoss
        """
        line = remove_comma(line)

        values = [
            ('-' + x[1:-1] if x[0] == '(' and x[-1] == ')' else x)
            for x in [x.replace('$', '') for x in line.split(',')]
        ]

        self.symbol = values[0]
        self.description = values[1]
        self.pl_open = values[2]
        self.pl_pct = values[3][:-1]
        self.pl_day = values[4]
        self.pl_ytd = values[5]
        self.margin_req = values[6]
        self.close_value = values[7]

        return self

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.symbol, self.description, self.pl_open, self.pl_pct, self.pl_day,
                   self.pl_ytd, self.margin_req, self.close_value]],
            index=[self.statement.date],
            columns=['Symbol', 'Description', 'P/L Open', 'P/L %', 'P/L Day',
                     'P/L YTD', 'Margin Req', 'Close Value']
        )

    def __unicode__(self):
        return '{symbol} {pl_open}'.format(
            symbol=self.symbol,
            pl_open=self.pl_open
        )

