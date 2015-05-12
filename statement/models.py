from django.db import models
from pandas import DataFrame


def replace_dash_in_quote(line):
    """
    Replace dash inside quote value
    :param line: str
    :return: str
    """
    if '"' in line:
        line = line.split('"')
        for k, i in enumerate(line):
            if k % 2 and ',' in i:
                line[k] = i.replace(',', '')

        line = ''.join(line)
    return line


class Statement(models.Model):
    """
    Account Summary
    Net Liquidating Value,"$49,141.69"
    Stock Buying Power,"$36,435.34"
    Option Buying Power,"$36,435.34"
    Commissions/Fees YTD,$159.08
    Futures Commissions YTD,$0.00 <-- skip futures
    """
    date = models.DateField()

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


class CashBalance(models.Model):
    """
    DATE,TIME,TYPE,REF #,DESCRIPTION,FEES,COMMISSIONS,AMOUNT,BALANCE
    1/29/15,01:00:00,BAL,,Cash balance at the start of business day 29.01 CST,,,,"50,000.00"
    1/29/15,14:35:49,LIQ,472251902,Cash liquidation,,,"75,000.00","125,000.00"
    """
    time = models.TimeField()
    name = models.CharField(max_length=20)
    ref_no = models.BigIntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    commission = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2)

    statement = models.ForeignKey(Statement, null=True)

    def load_csv(self, line):
        """
        Format cash_balance csv line data, save it and return object
        :param line: str
        :return: CashBalance
        """
        line = replace_dash_in_quote(line)

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


class AccountOrder(models.Model):
    """
    Notes,,Time Placed,Spread,Side,Qty,Pos Effect,Symbol,Exp,Strike,Type,PRICE,,TIF,Status
    ,,1/29/15 14:45:15,VERTICAL,SELL,-2,TO OPEN,EBAY,MAR 15,55,CALL,.73,LMT,DAY,CANCELED
    ,,,,BUY,+2,TO OPEN,EBAY,MAR 15,57.5,CALL,,,,
    """
    # todo: remove re row, fill below row if no re, do not save future and forex, fill stock carefully

    time_placed = models.TimeField()
    spread = models.CharField(max_length=50)
    side = models.CharField(max_length=4)
    qty = models.CharField(max_length=100)
    pos_effect = models.CharField(max_length=50)
    symbol = models.CharField(max_length=20)
    exp = models.CharField(max_length=50, null=True, blank=True)
    strike = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    contract = models.CharField(max_length=10, null=True, blank=True)
    price = models.DecimalField(max_digits=20, decimal_places=2)
    order = models.CharField(max_length=20)
    tif = models.CharField(max_length=20)
    status = models.TextField()

    statement = models.ForeignKey(Statement, null=True)

    def load_csv(self, line):
        """
        Format account_order csv line data, save it and return object
        :param line: str
        :return: HoldingEquity
        """
        line = replace_dash_in_quote(line)
        values = line.split(',')

        self.time_placed = values[2].split(' ')[1]
        self.spread = values[3]
        self.side = values[4]
        self.qty = values[5]
        self.pos_effect = values[6]
        self.symbol = values[7]
        self.exp = values[8] if values[8] else ''
        self.strike = values[9] if values[9] else 0.0
        self.contract = values[10]
        self.price = values[11]
        self.order = values[12]
        self.tif = values[13]
        self.status = values[14]

        return self

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.time_placed, self.spread, self.side, self.qty, self.pos_effect,
                   self.symbol, self.exp, self.strike if self.strike else '',
                   self.contract, self.price, self.order, self.tif, self.status]],
            index=[self.statement.date],
            columns=['Time Placed', 'Spread', 'Side', 'Qty', 'Pos Effect', 'Symbol',
                     'Exp', 'Strike', 'Type', 'PRICE', 'Order', 'TIF', 'Status']
        )


class AccountTrade(models.Model):
    """
    ,Exec Time,Spread,Side,Qty,Pos Effect,Symbol,Exp,Strike,Type,Price,Net Price,Order Type
    ,1/29/15 15:43:06,VERTICAL,SELL,-2,TO OPEN,EBAY,MAR 15,55,CALL,1.33,.80,LMT
    ,,,BUY,+2,TO OPEN,EBAY,MAR 15,57.5,CALL,.53,CREDIT,
    """
    # todo: remember to fill empty field in csv line, if stock, fill last 3 empty field only

    exec_time = models.TimeField()
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

    def load_csv(self, line):
        """
        Format account_trade csv line data, save it and return object
        :param line: str
        :return: HoldingEquity
        """
        line = replace_dash_in_quote(line)
        values = line.split(',')

        self.exec_time = values[1].split(' ')[1]
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
            data=[[self.exec_time, self.spread, self.side, self.qty, self.pos_effect,
                   self.symbol, self.exp, self.strike if self.strike else '',
                   self.contract, self.price, self.net_price, self.order_type]],
            index=[self.statement.date],
            columns=['Exec Time', 'Spread', 'Side', 'Qty', 'Pos Effect', 'Symbol',
                     'Exp', 'Strike', 'Type', 'Price', 'Net Price', 'Order Type']
        )


class HoldingEquity(models.Model):
    """
    Symbol,Description,Qty,Trade Price,Close Price,Close Value
    XOM,EXXON MOBIL CORPORATION COM,-100,87.05,87.58,"($8,758.00)"
    """
    symbol = models.CharField(max_length=20)
    description = models.TextField(max_length=500)
    qty = models.IntegerField()
    trade_price = models.DecimalField(max_digits=20, decimal_places=2)
    close_price = models.DecimalField(max_digits=20, decimal_places=2)
    close_value = models.DecimalField(max_digits=20, decimal_places=2)

    statement = models.ForeignKey(Statement, null=True)

    def load_csv(self, line):
        """
        Format holding_equity csv line data, save it and return object
        :param line: str
        :return: HoldingEquity
        """
        line = replace_dash_in_quote(line)

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

    def load_csv(self, line):
        """
        Format holding_option csv line data, save it and return object
        :param line: str
        :return: HoldingEquity
        """
        line = replace_dash_in_quote(line)

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


class ProfitLoss(models.Model):
    # todo: skip no trading, no pl day with no bp, futures
    """
    Symbol,Description,P/L Open,P/L %,P/L Day,P/L YTD,P/L Diff,Margin Req,Close Value
    XOM,EXXON MOBIL CORPORATION COM,($28.00),-0.31%,($28.00),($28.00),$0.00,"$1,313.70","($8,995.00)"
    """
    symbol = models.CharField(max_length=20)
    description = models.TextField(max_length=500)
    pl_open = models.DecimalField(max_digits=20, decimal_places=2)
    pl_pct = models.DecimalField(max_digits=20, decimal_places=2)
    pl_day = models.DecimalField(max_digits=20, decimal_places=2)
    pl_ytd = models.DecimalField(max_digits=20, decimal_places=2)
    margin_req = models.DecimalField(max_digits=20, decimal_places=2)
    close_value = models.DecimalField(max_digits=20, decimal_places=2)

    statement = models.ForeignKey(Statement, null=True)

    def load_csv(self, line):
        """
        Format profit_loss csv line data, save it and return object
        :param line: str
        :return: ProfitLoss
        """
        line = replace_dash_in_quote(line)

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
