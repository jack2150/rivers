import os
import re
import logging
from datetime import datetime
from django.db import models
from django.db.models import Q

from base.ufunc import ds
from rivers.settings import IB_STATEMENT_DIR

logger = logging.getLogger('views')

POS_VALUES = {
    'Prior Period Value': 'prior',
    'Transactions': 'trans',
    'MTM P/L On Prior Period': 'pl_mtm_prior',
    'MTM P/L On Transactions': 'pl_mtm_trans',
    'End Of Period Value': 'end'
}


class IBStatementName(models.Model):
    title = models.CharField(max_length=100)
    real_name = models.CharField(max_length=100)
    broker = models.CharField(max_length=100, default='Interactive brokers')
    account_id = models.CharField(max_length=50)
    account_type = models.CharField(max_length=200, default='Individual')
    customer_type = models.CharField(max_length=200, default='Individual')
    capability = models.CharField(max_length=200, default='Margin')
    path = models.CharField(max_length=100)
    start = models.DateField()
    stop = models.DateField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    @staticmethod
    def is_account(line):
        """
        Check is account statement
        :param line: list
        :return: bool
        """
        data = line.split(',')

        result = False
        if len(data) == 4:
            if data[0] == 'Account Information' and data[1] == 'Data':
                if data[2] in ('Name', 'Account', 'Account Capabilities'):
                    return True

        return result

    def match_account(self, lines):
        """
        Match is account statement name
        :param lines: list
        :return: bool
        """
        count = 0
        for line in lines:
            data = line.strip().split(',')

            if data[2] == 'Name' and data[3] == self.real_name:
                logger.info('BrokerName: %s' % data[3])
                count += 1

            if data[2] == 'Account' and data[3] == self.account_id:
                logger.info('Account: %s' % data[3])
                count += 1

            if data[2] == 'Account Capabilities' and data[3] == self.capability:
                logger.info('Account Capabilities: %s' % data[3])
                count += 1

        result = False
        if count == 3:
            result = True

        return result

    def __unicode__(self):
        return '{account_id} {capability}'.format(
            account_id=self.account_id, capability=self.capability
        )


class IBStatement(models.Model):
    """
    Change in NAV,Header,Field Name,Field Value
    Note: Legacy Full CSV only
    """
    statement_name = models.ForeignKey(IBStatementName)
    date = models.DateField()

    stock_prior = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    stock_trans = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    stock_pl_mtm_prior = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    stock_pl_mtm_trans = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    stock_end = models.DecimalField(default=0, max_digits=10, decimal_places=2)

    option_prior = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    option_trans = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    option_pl_mtm_prior = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    option_pl_mtm_trans = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    option_end = models.DecimalField(default=0, max_digits=10, decimal_places=2)

    unique_together = (('name', 'date'), )

    @staticmethod
    def is_change_position_value(line):
        """
        Check if line is Change in NAV
        :param line: str
        :return: bool
        """
        data = line.split(',')

        result = False
        if data[0] == 'Change in Position Value' and len(data) == 6:
            if data[1] == 'Data':
                return True

        return result

    def extract_csv(self, line):
        """
        Extract csv line into object data
        Change in Position Value,Data,STK,USD,End Of Period Value,5410.61
        Change in Position Value,Data,OPT,USD,Prior Period Value,-1172.29
        :param line: str
        :return: IBProfitLoss
        """
        data = line.split(',')

        if data[2] == 'STK':
            asset = 'stock'
        elif data[2] == 'OPT':
            asset = 'option'
        else:
            raise ValueError('Invalid column data: %s' % data[2])

        key = '%s_%s' % (asset, POS_VALUES[data[4]])
        setattr(self, key, round(float(data[5]), 2))

        return self

    def __unicode__(self):
        return '{name} {date}'.format(
            name=self.statement_name.account_id, date=self.date.strftime('%Y-%m-%d')
        )

    @staticmethod
    def is_statement(line):
        """
        Check is statement data line
        :return: bool
        """
        data = line.split(',')

        result = False
        if len(data) == 4:
            if data[0] == 'Statement' and data[2] in ('BrokerName', 'Title', 'Period'):
                result = True

        return result

    def match_statement(self, statement_lines):
        """
        Check statement object is same as csv file
        In order to match all, it need to sum up total 3
        :param statement_lines:
        :return: bool
        """
        count = 0
        for line in statement_lines:
            data = line.split(',')

            if data[2] == 'BrokerName' and 'Interactive Brokers' in data[3]:
                count += 1

            elif data[2] == 'Title' and 'Activity Statement' in data[3]:
                count += 1

            elif data[2] == 'Period':
                temp = data[3].split(' ')
                temp[1] = '%02d' % int(temp[1])
                date_str = ' '.join(temp).strip()
                d = datetime.strptime(date_str, '%B %d %Y').date()

                if self.date == d:
                    count += 1

        result = False
        if count == 3:
            result = True

            logger.info('BrokerName: %s' % 'Interactive Brokers')
            logger.info('Title: %s' % 'Activity Statement')
            logger.info('Period: %s == %s' % (ds(self.date), ds(self.date)))

        return result

    def statement_import(self, statement_name, year, fname, force=False):
        """
        Open a ib daily statement file
        then extract data from file and
        save into db
        :param statement_name: IBStatementName
        :param year: int
        :param fname: str
        :param force: bool
        :return: IBStatement
        """
        path = os.path.join(IB_STATEMENT_DIR, statement_name.path, year, fname)
        date = os.path.basename(path).split('_')[-1].split('.')[0]
        date = datetime.strptime(date, '%Y%m%d')

        # check data is duplicate
        ib_statements = IBStatement.objects.filter(
            Q(statement_name=statement_name) & Q(date=date)
        )
        if ib_statements.exists():
            if not force:
                logger.info('Statement name: %s Date: %s already exists!' % (
                    statement_name, date.date()
                ))
                return self
        else:
            self.statement_name = statement_name
            self.date = date
            self.save()

        lines = open(path).readlines()

        objects = {
            'ib_nav': IBNetAssetValue,
            'ib_mark': IBMarkToMarket,
            'ib_perform': IBPerformance,
            'ib_pl': IBProfitLoss,
            'ib_cash': IBCashReport,
            'ib_open_pos': IBOpenPosition,
            'ib_trade': IBPositionTrade,
            'ib_info': IBFinancialInfo,
            'ib_interest': IBInterestAccrual
        }
        ib_data = {
            'ib_nav': [],
            'ib_mark': [],
            'ib_perform': [],
            'ib_pl': [],
            'ib_cash': [],
            'ib_open_pos': [],
            'ib_trade': [],
            'ib_info': [],
            'ib_interest': [],
        }

        valid_account = False
        valid_statement = False
        account_lines = []
        statement_lines = []
        for line in lines:
            line = re.sub(r'(?!(([^"]*"){2})*[^"]*$),', '', line)  # remove ',' inside quote
            line = line.replace('--', '0')
            line = line.strip()

            # remove '"'
            data = line.split(',')
            temp = []
            for d in data:
                if len(d) > 2:
                    if d[0] == '"' and d[-1] == '"':
                        d = d[1:-1]

                temp.append(d)
            line = ','.join(temp)

            # check statement is same date, broker, statement
            if not valid_statement:
                if self.is_statement(line):
                    statement_lines.append(line)

                if len(statement_lines) == 3:
                    valid_statement = self.match_statement(statement_lines)
                else:
                    continue

            # check statement name is same account
            if not valid_account:
                if self.statement_name.is_account(line):
                    account_lines.append(line)

                if len(account_lines) == 3:
                    valid_account = self.statement_name.match_account(account_lines)
                else:
                    continue

            if self.is_change_position_value(line):
                # print line
                self.extract_csv(line)

            elif IBNetAssetValue.is_object(line):
                # print line.strip()
                ib_nav = IBNetAssetValue()
                ib_nav = ib_nav.extract_csv(self, line)

                ib_data['ib_nav'].append(ib_nav)

            elif IBMarkToMarket.is_object(line):
                # print line.strip()
                ib_mark = IBMarkToMarket()
                ib_mark = ib_mark.extract_csv(self, line)

                ib_data['ib_mark'].append(ib_mark)

            elif IBPerformance.is_object(line):
                # print line.strip()
                ib_perform = IBPerformance()
                ib_perform = ib_perform.extract_csv(self, line)

                ib_data['ib_perform'].append(ib_perform)

            elif IBProfitLoss.is_object(line):
                # print line.strip()
                ib_pl = IBProfitLoss()
                ib_pl = ib_pl.extract_csv(self, line)

                ib_data['ib_pl'].append(ib_pl)

            elif IBCashReport.is_object(line):
                # print line.strip()
                ib_cash = IBCashReport()
                ib_cash = ib_cash.extract_csv(self, line)

                ib_data['ib_cash'].append(ib_cash)

            elif IBOpenPosition.is_object(line):
                # print line.strip()
                ib_open_pos = IBOpenPosition()
                ib_open_pos = ib_open_pos.extract_csv(self, line)

                ib_data['ib_open_pos'].append(ib_open_pos)

            elif IBPositionTrade.is_object(line):
                # print line.strip()
                ib_trade = IBPositionTrade()
                ib_trade = ib_trade.extract_csv(self, line)

                ib_data['ib_trade'].append(ib_trade)

            elif IBFinancialInfo.is_object(line):
                # print line.strip()
                ib_info = IBFinancialInfo()
                ib_info = ib_info.extract_csv(self, line)

                ib_data['ib_info'].append(ib_info)

            elif IBInterestAccrual.is_object(line):
                ib_interest = IBInterestAccrual()
                ib_interest = ib_interest.extract_csv(self, line)

                ib_data['ib_interest'].append(ib_interest)
            else:
                # print 'SKIP', line.strip()
                pass

        # save
        for key in ib_data.keys():
            if len(ib_data[key]):
                objects[key].objects.bulk_create(ib_data[key])
                logger.info('IBStatement %s object bulk_create %d' % (key, len(ib_data[key])))

        # save ib statement
        self.save()
        logger.info('IBStatement import saved')

        return self


class IBPosition(models.Model):
    statement_name = models.ForeignKey(IBStatementName)

    symbol = models.CharField(max_length=20)
    date0 = models.DateField()
    date1 = models.DateField(null=True, blank=True, default=None)
    status = models.CharField(
        choices=(('open', 'Open'), ('close', 'Close'), ('expire', 'Expire')),
        default='open', max_length=50,
    )

    # for extra detail, auto generate
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    options = models.BooleanField(default=False)
    perform = models.CharField(
        max_length=50, default='unknown', choices=(
            ('profit', 'Profit'),
            ('even', 'Even'),
            ('loss', 'Loss'),
            ('unknown', 'Unknown'),
        )
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # spread, self select
    updated = models.BooleanField(default=False, help_text='Add extra info?')
    adjust = models.BooleanField(default=False, help_text='Trade adjusted?')
    qty_multiply = models.IntegerField(default=0)
    move = models.CharField(
        max_length=50, default='neutral', choices=(
            ('bull', 'Bull'),
            ('neutral_bull', 'Neutral to bull'),
            ('neutral', 'Neutral'),
            ('neutral_bear', 'Neutral to bear'),
            ('bear', 'Bear'),
        )
    )
    side = models.CharField(
        max_length=20, default='long', choices=(
            ('long', 'Long'),
            ('short', 'Short'),
        )
    )
    account = models.CharField(
        max_length=20, default='debit', choices=(
            ('debit', 'Debit'),
            ('credit', 'Credit'),
        )
    )
    name = models.CharField(
        max_length=50, default='custom', choices=(
            ('stock', 'STOCK'),
            ('etf', 'ETF'),
            ('single', 'SINGLE'),
            ('covered', 'COVERED'),
            ('vertical', 'VERTICAL'),
            ('strangle', 'STRANGLE'),
            ('straddle', 'STRADDLE'),
            ('calendar', 'CALENDAR'),
            ('diagonal', 'DIAGONAL'),
            ('combo', 'COMBO'),
            ('ratio', 'RATIO'),
            ('butterfly', 'BUTTERFLY'),
            ('iron_butterfly', 'IRON_BUTTERFLY'),
            ('condor', 'CONDOR'),
            ('iron_condor', 'IRON_CONDOR'),
            ('custom', 'CUSTOM'),
        )
    )
    spread = models.CharField(
        max_length=50, default='', help_text='Full spread name'
    )
    strikes = models.CharField(
        max_length=50, default='', help_text='Example: 10/12/15'
    )

    # unique
    unique_together = (('symbol', 'date0'),)

    def __unicode__(self):
        return 'IBPosition {symbol} {date} {status}'.format(
            symbol=self.symbol,
            date=self.date0 if self.status == 'open' else self.date1,
            status=self.status
        )


class IBNetAssetValue(models.Model):
    statement = models.ForeignKey(IBStatement)

    asset = models.CharField(max_length=20)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    total_long = models.DecimalField(max_digits=10, decimal_places=2)
    total_short = models.DecimalField(max_digits=10, decimal_places=2)
    total_prior = models.DecimalField(max_digits=10, decimal_places=2)
    total_change = models.DecimalField(max_digits=10, decimal_places=2)

    @staticmethod
    def is_object(line):
        """
        Check if line is IBNetAssetValue
        :param line: str
        :return: bool
        """
        data = line.split(',')

        result = False
        if 'Net Asset Value' in data[0] and len(data) == 8:
            if data[1] == 'Data':
                return True

        return result

    def extract_csv(self, ib_statement, line):
        """
        Extract csv line into object data
        :param ib_statement: IBStatement
        :param line: str
        :return: IBNetAssetValue
        """
        data = line.split(',')

        self.statement = ib_statement
        self.asset = data[2].strip().lower()  # change
        self.total = float(data[3])
        self.total_long = float(data[4])
        self.total_short = float(data[5])
        self.total_prior = float(data[6])
        self.total_change = float(data[7])

        return self

    def __unicode__(self):
        """
        Output data
        :return: str
        """
        return 'IBNetAssetValue {asset} {total1} {change}'.format(
            asset=self.asset,
            total1=self.total,
            change=self.total_change
        )


class IBMarkToMarket(models.Model):
    statement = models.ForeignKey(IBStatement)

    symbol = models.CharField(max_length=20)
    options = models.BooleanField(default=False)
    ex_date = models.DateField(null=True, blank=True, default=None)
    strike = models.FloatField(default=None, null=True, blank=True)
    name = models.CharField(max_length=1, default=None, null=True, blank=True)

    qty0 = models.IntegerField(default=0)
    qty1 = models.IntegerField(default=0)
    price0 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price1 = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    pl_pos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pl_trans = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pl_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pl_other = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pl_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # foreign key
    position = models.ForeignKey(IBPosition, default=None, null=True, blank=True)

    @staticmethod
    def is_object(line):
        """
        Check if line is IBMarkToMarket
        :param line: str
        :return: bool
        """
        data = line.split(',')

        result = False
        if data[0] == 'Mark-to-Market Performance Summary' and len(data) == 14:
            if data[1] == 'Data' and data[2] != 'Forex' and 'Total' not in data[2]:
                if all([x not in data[2] for x in ('Return', 'Fee', 'Interest')]):
                    return True

        return result

    def extract_csv(self, ib_statement, line):
        """
        Extract csv line into object data
        :param ib_statement: IBStatement
        :param line: str
        :return: IBMarkToMarket
        """
        data = line.split(',')

        self.statement = ib_statement
        symbol = data[3].split(' ')
        if len(symbol) == 4:
            self.options = True
            self.symbol = symbol[0]
            self.ex_date = datetime.strptime(symbol[1], '%d%b%y')
            self.strike = symbol[2]
            self.name = symbol[3]
        else:
            self.symbol = symbol[0]

        self.qty0 = int(data[4])
        self.qty1 = int(data[5])

        if data[6] != '--':
            self.price0 = float(data[6])

        self.price1 = float(data[7])
        self.pl_pos = float(data[8])
        self.pl_trans = float(data[9])
        self.pl_fee = float(data[10])
        self.pl_other = float(data[11])
        self.pl_total = float(data[12])

        return self

    def __unicode__(self):
        if self.statement.id:
            return 'IBMarkToMarket {symbol} {date} {pl_total}'.format(
                symbol=self.symbol, date=self.statement.date.strftime('%Y-%m-%d'),
                pl_total=self.pl_total
            )
        else:
            return 'IBMarkToMarket {symbol} {pl_total}'.format(
                symbol=self.symbol, pl_total=self.pl_total
            )


class IBPerformance(models.Model):
    statement = models.ForeignKey(IBStatement)

    symbol = models.CharField(max_length=20)
    options = models.BooleanField(default=False)
    ex_date = models.DateField(null=True, blank=True, default=None)
    strike = models.FloatField(default=None, null=True, blank=True)
    name = models.CharField(max_length=1, default=None, null=True, blank=True)

    cost_adj = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    real_st_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # short term
    real_st_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    real_lt_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # long term
    real_lt_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    real_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    unreal_st_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # short term
    unreal_st_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unreal_lt_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # long term
    unreal_lt_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unreal_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # foreign key
    position = models.ForeignKey(IBPosition, default=None, null=True, blank=True)

    @staticmethod
    def is_object(line):
        """
        Check if line is IBPerformance
        :param line: str
        :return: bool
        """
        data = line.split(',')

        result = False
        if data[0] == 'Realized & Unrealized Performance Summary' and len(data) == 17:
            if data[1] == 'Data' and 'Total' not in data[2]:
                return True

        return result

    def extract_csv(self, ib_statement, line):
        """
        Extract csv line into object data
        :param ib_statement: IBStatement
        :param line: str
        :return: IBPerformance
        """
        data = line.split(',')

        self.statement = ib_statement

        symbol = data[3].split(' ')
        if len(symbol) == 4:
            self.options = True
            self.symbol = symbol[0]
            self.ex_date = datetime.strptime(symbol[1], '%d%b%y')
            self.strike = symbol[2]
            self.name = symbol[3]
        else:
            self.symbol = symbol[0]

        self.cost_adj = data[4]
        self.real_st_profit = float(data[5])
        self.real_st_loss = float(data[6])
        self.real_lt_profit = float(data[7])
        self.real_lt_loss = float(data[8])
        self.real_total = float(data[9])
        self.unreal_st_profit = float(data[10])
        self.unreal_st_loss = float(data[11])
        self.unreal_lt_profit = float(data[12])
        self.unreal_lt_loss = float(data[13])
        self.unreal_total = float(data[14])
        self.total = float(data[15])

        return self

    def __unicode__(self):
        if self.statement.id:
            return 'IBPerformance {symbol} {date} {total}'.format(
                symbol=self.symbol, date=self.statement.date.strftime('%Y-%m-%d'),
                total=self.total
            )
        else:
            return 'IBPerformance {symbol} {total}'.format(
                symbol=self.symbol, total=self.total
            )


class IBProfitLoss(models.Model):
    """
    Only available at end of month
    Month & Year to Date Performance Summary == Profit Loss
    Month & Year to Date Performance Summary,
    Header,Asset Category,Symbol,Description,Mark-to-Market MTD,Mark-to-Market YTD,
    Realized S/T MTD,Realized S/T YTD,Realized L/T MTD,Realized L/T YTD
    """
    statement = models.ForeignKey(IBStatement)

    asset = models.CharField(max_length=20)

    symbol = models.CharField(max_length=20)
    options = models.BooleanField(default=False)
    option_code = models.CharField(max_length=100, default=None, null=True, blank=True)

    company = models.CharField(max_length=200, default=None, blank=True, null=True)
    ex_date = models.DateField(null=True, blank=True, default=None)
    strike = models.FloatField(default=None, null=True, blank=True)
    name = models.CharField(max_length=1, default=None, null=True, blank=True)

    pl_mtd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pl_ytd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    real_st_mtd = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # short term
    real_st_ytd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    real_lt_mtd = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # long term
    real_lt_ytd = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # foreign key
    position = models.ForeignKey(IBPosition, default=None, null=True, blank=True)

    @staticmethod
    def is_object(line):
        """
        Check is profit loss line
        :param line: str
        :return: bool
        """
        data = line.split(',')

        if data[0] == 'Month & Year to Date Performance Summary' and len(data) == 11:
            if data[1] == 'Data' and 'Total' not in data[2]:
                return True
        else:
            return False

    def extract_csv(self, ib_statement, line):
        """
        Extract csv line into object data
        :param ib_statement: IBStatement
        :param line: str
        :return: IBProfitLoss
        """
        data = line.split(',')

        self.statement = ib_statement

        if data[2] == 'Equity and Index Options':
            self.asset = 'options'
        else:
            self.asset = data[2].lower()

        symbol = ' '.join(data[3].split()).split(' ')
        if len(symbol) == 2:
            self.options = True
            self.symbol = symbol[0]
            self.option_code = symbol[1]  # 170106C00034000
        else:
            self.symbol = symbol[0]

        options = data[4].split(' ')
        if len(options) == 4 and options[3] in ('C', 'P') and options[0] == self.symbol:
            self.options = True
            self.ex_date = datetime.strptime(options[1], '%d%b%y')
            self.strike = options[2]
            self.name = options[3]

            self.company = ''
        else:
            self.company = data[4]

        self.pl_mtd = round(float(data[5]), 2)
        self.pl_ytd = float(data[6])
        self.real_st_mtd = float(data[7])
        self.real_st_ytd = float(data[8])
        self.real_lt_mtd = float(data[9])
        self.real_lt_ytd = float(data[10])

        return self

    def __unicode__(self):
        if self.statement.id:
            return 'IBProfitLoss {symbol} {date} {pl_ytd}'.format(
                symbol=self.symbol, date=self.statement.date.strftime('%Y-%m-%d'),
                pl_ytd=self.pl_ytd
            )
        else:
            return 'IBProfitLoss {symbol} {pl_ytd}'.format(
                symbol=self.symbol, pl_ytd=self.pl_ytd
            )


class IBCashReport(models.Model):
    statement = models.ForeignKey(IBStatement)

    summary = models.CharField(max_length=50)
    currency = models.CharField(max_length=100, default='Base Currency Summary')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    security = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    future = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pl_mtd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pl_ytd = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @staticmethod
    def is_object(line):
        """
        Check csv line is CashReport
        :param line: str
        :return: bool
        """
        data = line.split(',')

        if data[0] == 'Cash Report' and len(data) in (8, 10):
            if data[1] == 'Data':
                return True
        else:
            return False

    def extract_csv(self, ib_statement, line):
        """
        Extract csv line into object data
        :param ib_statement: IBStatement
        :param line: str
        :return: IBProfitLoss
        """
        data = line.split(',')

        self.statement = ib_statement
        self.summary = data[2].strip()
        self.currency = data[3].strip()
        self.total = float(data[4])

        if data[5] != '':
            self.security = float(data[5])

        if data[6] != '':
            self.future = float(data[6])

        if len(data) == 10:
            if data[7] != '':
                self.pl_mtd = float(data[7])

            if data[8] != '':
                self.pl_ytd = float(data[8])

        return self

    def __unicode__(self):
        if self.statement.id:
            return 'IBCashReport {name} {date} {pl_ytd}'.format(
                name=self.summary, date=self.statement.date.strftime('%Y-%m-%d'),
                pl_ytd=self.pl_ytd
            )
        else:
            return 'IBCashReport {name} {pl_ytd}'.format(
                name=self.summary, pl_ytd=self.pl_ytd
            )


class IBOpenPosition(models.Model):
    statement = models.ForeignKey(IBStatement)

    side = models.CharField(max_length=10, default='long')
    asset = models.CharField(max_length=50, default='stocks')
    currency = models.CharField(max_length=20, default='USD')

    symbol = models.CharField(max_length=20)
    options = models.BooleanField(default=False)
    ex_date = models.DateField(null=True, blank=True, default=None)
    strike = models.FloatField(default=None, null=True, blank=True)
    name = models.CharField(max_length=1, default=None, null=True, blank=True)

    # date_time = models.DateTimeField(blank=True, default=None, null=True)
    qty = models.IntegerField(default=0)
    multiplier = models.FloatField(default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_basic = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    close_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unreal_pl = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    nav_pct = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # foreign key
    position = models.ForeignKey(IBPosition, default=None, null=True, blank=True)

    @staticmethod
    def is_object(line):
        """
        Check csv line is OpenPosition
        :param line: str
        :return: bool
        """
        data = line.split(',')

        if 'Open Positions' in data[0] and len(data) == 16:
            if data[1] == 'Data' and data[2] == 'Summary' and 'Total' not in data[2]:
                return True
        else:
            return False

    def extract_csv(self, ib_statement, line):
        """
        Extract csv line into object data
        :param ib_statement: IBStatement
        :param line: str
        :return: IBOpenPosition
        """
        line = re.sub(r'(?!(([^"]*"){2})*[^"]*$),', '', line)  # remove ',' inside quote
        data = line.split(',')

        self.statement = ib_statement

        if 'Long' in data[0]:
            self.side = 'long'
        else:
            self.side = 'short'

        if data[3] == 'Equity and Index Options':
            self.asset = 'options'
        else:
            self.asset = data[3].lower()

        self.currency = data[4]

        symbol = data[5].split(' ')
        if len(symbol) == 4:
            self.options = True
            self.symbol = symbol[0]
            self.ex_date = datetime.strptime(symbol[1], '%d%b%y')
            self.strike = symbol[2]
            self.name = symbol[3]
        else:
            self.symbol = data[5]

        # if data[5] != '-':
        #     dt_str = data[5].replace('"', '')
        #     dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        #     self.date_time = dt

        self.qty = int(data[7])

        if data[8] != '':
            self.multiplier = data[8]

        self.cost_price = float(data[9]) if data[9] != '' else 0
        self.cost_basic = float(data[10]) if data[10] != '' else 0
        self.close_price = float(data[11]) if data[11] != '' else 0
        self.total_value = float(data[12]) if data[12] != '' else 0
        self.unreal_pl = float(data[13]) if data[13] != '' else 0
        self.nav_pct = float(data[14]) if data[14] != '' else 0

        return self

    def __unicode__(self):
        if self.statement.id:
            return 'IBOpenPosition {symbol} {date} {close_price}'.format(
                symbol=self.symbol, date=self.statement.date.strftime('%Y-%m-%d'),
                close_price=self.close_price
            )
        else:
            return 'IBOpenPosition {symbol} {close_price}'.format(
                symbol=self.symbol, close_price=self.close_price
            )


class IBPositionTrade(models.Model):
    statement = models.ForeignKey(IBStatement)

    order = models.CharField(max_length=20, default='trade')
    asset = models.CharField(max_length=20)
    currency = models.CharField(max_length=20, default='USD')

    symbol = models.CharField(max_length=20)
    options = models.BooleanField(default=False)
    ex_date = models.DateField(null=True, blank=True, default=None)
    strike = models.FloatField(default=None, null=True, blank=True)
    name = models.CharField(max_length=1, default=None, null=True, blank=True)

    date_time = models.DateTimeField()
    exchange = models.CharField(max_length=100, default='AUTO', blank=True)
    qty = models.IntegerField(default=0)
    trade_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    proceed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    real_pl = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mtm_pl = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # foreign key
    position = models.ForeignKey(IBPosition, default=None, null=True, blank=True)

    @staticmethod
    def is_object(line):
        """
        Check csv line is IBPositionTrade
        :param line: str
        :return: bool
        """
        line = re.sub(r'(?!(([^"]*"){2})*[^"]*$),', '', line)  # remove ',' inside quote
        data = line.split(',')

        if data[0] == 'Trades' and len(data) == 17:
            if data[1] == 'Data' and data[2] != 'Total' and 'Total' not in data[4]:
                if ' ' not in data[4] and len(data[6]) and data[2] in ('Trade', 'Order'):
                    # datetime must exists
                    return True
        else:
            return False

    def extract_csv(self, ib_statement, line):
        """
        Extract csv line into object data
        :param ib_statement: IBStatement
        :param line: str
        :return: IBOpenPosition
        """
        line = re.sub(r'(?!(([^"]*"){2})*[^"]*$),', '', line)  # remove ',' inside quote
        data = line.split(',')

        self.statement = ib_statement
        self.order = data[2]

        if data[3] == 'Equity and Index Options':
            self.asset = 'options'
        else:
            self.asset = data[3].lower()
            
        self.currency = data[4]

        symbol = data[5].split(' ')
        if len(symbol) == 4:
            self.options = True
            self.symbol = symbol[0]
            self.ex_date = datetime.strptime(symbol[1], '%d%b%y')
            self.strike = symbol[2]
            self.name = symbol[3]
        else:
            self.symbol = data[5]

        if data[6] != '-':
            dt = datetime.strptime(data[6], '%Y-%m-%d %H:%M:%S')
            self.date_time = dt

        if data[7] != '-':
            self.exchange = data[7]

        self.qty = int(data[8])
        self.trade_price = float(data[9])
        self.cost_price = float(data[10])
        self.proceed = float(data[11])
        self.fee = float(data[12])
        self.real_pl = float(data[13])
        self.mtm_pl = float(data[14])

        return self

    def __unicode__(self):
        # BUY +2 BUTTERFLY CLF 100 17 MAR 17 12/10/9 PUT @.58 LMT FIXED
        name = '%+d %.2f' % (self.qty, self.cost_price)
        if self.options:
            name = '%+d %s 100 %s %s %s @%.2f LMT' % (
                self.qty, self.symbol, self.ex_date.strftime('%d %b %y').upper(),
                self.strike, self.name, self.trade_price
            )

        if self.statement.id:
            return 'IBPositionTrade {symbol} {date} {name}'.format(
                symbol=self.symbol,
                date=self.statement.date.strftime('%Y-%m-%d'),
                name=name
            )
        else:
            return 'IBPositionTrade {symbol} {name}'.format(
                symbol=self.symbol,
                name=name
            )


class IBFinancialInfo(models.Model):
    statement = models.ForeignKey(IBStatement)

    asset = models.CharField(max_length=20)
    symbol = models.CharField(max_length=20)
    company = models.CharField(max_length=200)
    con_id = models.IntegerField(default=0)
    sec_id = models.CharField(max_length=50)
    multiplier = models.FloatField(default=0)

    # Expiry,Delivery Month,Type,Strike,Code
    options = models.BooleanField(default=False)
    ex_date = models.DateField(null=True, blank=True, default=None)
    ex_month = models.DateField(null=True, blank=True, default=None)
    name = models.CharField(max_length=1, default=None, null=True, blank=True)
    strike = models.FloatField(default=None, null=True, blank=True)

    # foreign key
    position = models.ForeignKey(IBPosition, default=None, null=True, blank=True)

    @staticmethod
    def is_object(line):
        """
        Check csv line is IBFinancialInfo
        :param line: str
        :return: bool
        """
        data = line.split(',')

        if data[0] == 'Financial Instrument Information' and len(data) in (9, 12):
            if data[1] == 'Data':
                return True
        else:
            return False

    def extract_csv(self, ib_statement, line):
        """
        Extract csv line into object data
        :param ib_statement: IBStatement
        :param line: str
        :return: IBOpenPosition
        """
        line = re.sub(r'(?!(([^"]*"){2})*[^"]*$),', '', line)  # remove ',' inside quote
        data = line.split(',')

        self.statement = ib_statement

        if len(data) == 9:
            # Financial Instrument Information,Header,Asset Category,Symbol,Description,Conid,
            # Security ID,Multiplier,Code
            self.asset = data[2].lower()
            self.symbol = data[3]
            self.company = data[4]

            if data[5] != '':
                self.con_id = int(data[5])

            if data[6] != '':
                self.sec_id = data[6]

            if data[7] != '':
                self.multiplier = int(data[7])

        elif len(data) == 12:
            # Financial Instrument Information,Header,Asset Category,Symbol,Description,Conid,
            # Multiplier,Expiry,Delivery Month,Type,Strike,Code
            self.options = True
            self.asset = 'options'

            symbol = data[3].split(' ')
            self.symbol = symbol[0]

            self.company = ''

            if data[5] != '':
                self.con_id = int(data[5])

            if data[6] != '':
                self.multiplier = int(data[6])

            self.ex_date = datetime.strptime(data[7], '%Y-%m-%d')
            self.ex_month = datetime.strptime(data[8], '%Y-%m')
            self.name = data[9]
            self.strike = data[10]

        return self

    def __unicode__(self):
        if self.statement.id:
            return 'IBFinancialInfo {symbol} {date}'.format(
                symbol=self.symbol, date=self.statement.date.strftime('%Y-%m-%d')
            )
        else:
            return 'IBFinancialInfo {symbol}'.format(
                symbol=self.symbol
            )


class IBInterestAccrual(models.Model):
    statement = models.ForeignKey(IBStatement)

    currency = models.CharField(max_length=100, default='Base Currency Summary')
    summary = models.CharField(max_length=50)
    interest = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @staticmethod
    def is_object(line):
        """
        Check csv line is CashReport
        :param line: str
        :return: bool
        """
        data = line.split(',')

        if data[0] == 'Interest Accruals' and len(data) == 5:
            if data[1] == 'Data':
                return True
        else:
            return False

    def extract_csv(self, ib_statement, line):
        """
        Extract csv line into object data
        :param ib_statement: IBStatement
        :param line: str
        :return: IBInterestAccrual
        """
        data = line.split(',')

        self.statement = ib_statement
        self.currency = data[2].strip()
        self.summary = data[3].strip()
        self.interest = float(data[4])

        return self

    def __unicode__(self):
        if self.statement.id:
            return 'IBInterestAccrual {name} {date} {interest}'.format(
                name=self.summary, date=self.statement.date.strftime('%Y-%m-%d'),
                interest=self.interest
            )
        else:
            return 'IBInterestAccrual {name} {interest}'.format(
                name=self.summary, interest=self.interest
            )
