from HTMLParser import HTMLParser
from StringIO import StringIO
from django.db import models
import pandas as pd
from urllib2 import urlopen


class MarketOpinion(models.Model):
    """
    Everyday spy opinion that use for trading
    economics calendar, special market news
    """
    date = models.DateField(
        help_text='Check /ES /NQ /YM /TF /VX'
    )

    # whole market
    volatility = models.CharField(
        max_length=20,
        choices=(('INCREASE', 'INCREASE'), ('NORMAL', 'NORMAL'), ('DECREASE', 'DECREASE')),
        help_text='Market volatility /VX or VIX'
    )

    bond = models.CharField(
        max_length=20,
        choices=(('BULL', 'BULL'), ('RANGE', 'RANGE'), ('BEAR', 'BEAR')),
        help_text='Bond market /TF'
    )

    commodity = models.CharField(
        max_length=20,
        choices=(('BULL', 'BULL'), ('RANGE', 'RANGE'), ('BEAR', 'BEAR')),
        help_text='Commodity /CL /NG /GC /SI'
    )

    currency = models.CharField(
        max_length=20,
        choices=(('BULL', 'BULL'), ('RANGE', 'RANGE'), ('BEAR', 'BEAR')),
        help_text='Forex /6J /DX /6E'
    )

    # technical trend, spy only
    short_trend0 = models.CharField(
        max_length=20,
        choices=(('BULL', 'BULL'), ('RANGE', 'RANGE'), ('BEAR', 'BEAR')),
        help_text='Previous short term trend'
    )
    short_trend1 = models.CharField(
        max_length=20,
        choices=(('BULL', 'BULL'), ('RANGE', 'RANGE'), ('BEAR', 'BEAR')),
        help_text='Current short term trend'
    )
    long_trend0 = models.CharField(
        max_length=20,
        choices=(('BULL', 'BULL'), ('RANGE', 'RANGE'), ('BEAR', 'BEAR')),
        help_text='Previous long term trend'
    )
    long_trend1 = models.CharField(
        max_length=20,
        choices=(('BULL', 'BULL'), ('RANGE', 'RANGE'), ('BEAR', 'BEAR')),
        help_text='Current long term trend'
    )

    short_persist = models.BooleanField(default=False)
    long_persist = models.BooleanField(default=False)

    description = models.TextField(
        null=True, blank=True, help_text='Input price expectation here'
    )

    # economics calendar
    market_indicator = models.IntegerField(default=0)
    extra_attention = models.IntegerField(default=0)
    key_indicator = models.IntegerField(default=0)

    special_news = models.BooleanField(default=False)

    commentary = models.TextField(
        null=True, blank=True, help_text='Input daily market condition'
    )


class EnterOpinion(models.Model):
    symbol = models.CharField(max_length=20)
    date = models.DateField()

    # final, score and trade or not
    score = models.IntegerField(default=0, max_length=2, help_text='Score for checklist items!')
    complete = models.BooleanField(default=False, help_text='Is checklist complete?')
    trade = models.BooleanField(default=False, help_text='Trade or not trade this position?')

    # position
    risk_profile = models.CharField(
        max_length=20, choices=(
            ('LOW', 'LOW'), ('NORMAL', 'NORMAL'), ('HIGH', 'HIGH')
        ),
        help_text='Risk you willing to take for this position'
    )

    bp_effect = models.DecimalField(max_digits=10, decimal_places=2)
    profit = models.DecimalField(max_digits=10, decimal_places=2)
    loss = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.IntegerField()

    strategy = models.CharField(max_length=50, help_text='Strategy name for this trade')
    spread = models.CharField(
        max_length=20,
        choices=(
            ('CREDIT', 'CREDIT'), ('DEBIT', 'DEBIT')
        ),
        help_text='Credit or debit spread'
    )
    optionable = models.BooleanField(default=False)

    enter_date = models.DateField()
    exit_date = models.DateField()

    # trade signal
    signal = models.CharField(
        max_length=20,
        choices=(('BULL', 'BULL'), ('RANGE', 'RANGE'), ('BEAR', 'BEAR'))
    )
    event = models.BooleanField(default=False, help_text='Event signal trade?')
    significant = models.BooleanField(
        default=False,
        help_text='Is signal have significant result?'
    )
    confirm = models.BooleanField(
        default=False,
        help_text='Is signal have confirm price movement?'
    )
    target = models.DecimalField(max_digits=10, decimal_places=2)

    market = models.CharField(
        max_length=20,
        choices=(('MAJOR', 'MAJOR'), ('BOND', 'BOND'), ('COMMODITY', 'COMMODITY'),
                 ('CURRENCY', 'CURRENCY')),
        help_text='Underlying indices category'
    )

    description = models.TextField(null=True, blank=True)

    # event happen between enter and exit date
    earning = models.BooleanField(default=False, help_text='Earning between enter until exit date?')
    dividend = models.BooleanField(default=False, help_text='Dividend between enter until exit date?')
    split = models.BooleanField(default=False, help_text='Split between enter until exit date?')
    announcement = models.BooleanField(
        default=False, help_text='Announcement between enter until exit date?'
    )

    # news
    news_level = models.CharField(
        max_length=20,
        choices=(('WEAK', 'WEAK'), ('NORMAL', 'NORMAL'), ('STRONG', 'STRONG'))
    )
    news_signal = models.CharField(
        max_length=20,
        choices=(('BULL', 'BULL'), ('UNKNOWN', 'UNKNOWN'), ('BEAR', 'BEAR'))
    )

    # direct charts indicator
    long_trend0 = models.CharField(
        max_length=20,
        choices=(('BULL', 'BULL'), ('RANGE', 'RANGE'), ('BEAR', 'BEAR')),
        help_text='Previous long term price trend'
    )
    long_trend1 = models.CharField(
        max_length=20,
        choices=(('BULL', 'BULL'), ('RANGE', 'RANGE'), ('BEAR', 'BEAR')),
        help_text='Current long term price trend'
    )
    short_trend0 = models.CharField(
        max_length=20,
        choices=(('BULL', 'BULL'), ('RANGE', 'RANGE'), ('BEAR', 'BEAR')),
        help_text='Previous short term price trend'
    )
    short_trend1 = models.CharField(
        max_length=20,
        choices=(('BULL', 'BULL'), ('RANGE', 'RANGE'), ('BEAR', 'BEAR')),
        help_text='Current short term price trend'
    )
    long_persist = models.BooleanField(default=False, help_text='Is current long trend continue?')
    short_persist = models.BooleanField(default=False, help_text='Is current short trend continue?')

    # institutional ownership
    ownership = models.BooleanField(default=False)
    ownership_holding_pct = models.FloatField(null=True, blank=True)
    ownership_sell_count = models.IntegerField(null=True, blank=True, max_length=10)
    ownership_sell_share = models.BigIntegerField(null=True, blank=True)
    ownership_held_count = models.IntegerField(null=True, blank=True, max_length=10)
    ownership_held_share = models.BigIntegerField(null=True, blank=True)
    ownership_buy_count = models.IntegerField(null=True, blank=True)
    ownership_buy_share = models.BigIntegerField(null=True, blank=True)
    ownership_na = models.BigIntegerField(null=True, blank=True)
    ownership_na_pct = models.FloatField(null=True, blank=True)

    # mostly retail holder
    ownership_new_count = models.IntegerField(null=True, blank=True)
    ownership_new_share = models.BigIntegerField(null=True, blank=True)
    ownership_out_count = models.IntegerField(null=True, blank=True)
    ownership_out_share = models.BigIntegerField(null=True, blank=True)

    # top 15 movement
    ownership_top15_sum = models.FloatField(null=True, blank=True)
    ownership_top15_na_pct = models.FloatField(null=True, blank=True)

    # insider trade
    insider = models.BooleanField(default=False)
    insider_buy_3m = models.IntegerField(null=True, blank=True)
    insider_buy_12m = models.IntegerField(null=True, blank=True)
    insider_sell_3m = models.IntegerField(null=True, blank=True)
    insider_sell_12m = models.IntegerField(null=True, blank=True)

    insider_buy_share_3m = models.BigIntegerField(null=True, blank=True)
    insider_buy_share_12m = models.BigIntegerField(null=True, blank=True)
    insider_sell_share_3m = models.BigIntegerField(null=True, blank=True)
    insider_sell_share_12m = models.BigIntegerField(null=True, blank=True)
    insider_na_3m = models.BigIntegerField(null=True, blank=True)
    insider_na_12m = models.BigIntegerField(null=True, blank=True)

    # short interest
    short_interest = models.BooleanField(default=False)
    df_short_interest = models.TextField(
        null=True, blank=True, help_text='Short interest dataframe'
    )
    short_squeeze = models.BooleanField(default=False)

    # analyst rating
    analyst_rating = models.BooleanField(default=False)
    abr_current = models.FloatField(
        null=True, blank=True, help_text='Average brokerage rating, less is better'
    )
    abr_previous = models.FloatField(
        null=True, blank=True, help_text='Last brokerage rating'
    )
    abr_target = models.DecimalField(
        null=True, blank=True, max_digits=10, decimal_places=2, help_text='Average target price'
    )
    abr_rating_count = models.IntegerField(null=True, blank=True, help_text='Number of recommendations.')

    def get_ownership(self):
        """
        Download data from nasdaq html online
        No Institutional Holdings for this security
        """
        # first get institute holding
        response = urlopen(
            'http://www.nasdaq.com/symbol/{symbol}/institutional-holdings'.format(
                symbol=self.symbol.lower()
            )
        )
        html = response.read()
        lines = html.split('\r\n')
        #html = open(r'C:\Users\Jack\Downloads\111.html').read()
        #lines = html.split('\n')

        f = lambda x: lines.index([l for l in lines if x in l].pop())
        c = lambda x: x[x.index('>') + 1:x.rindex('<')].replace(',', '')

        if 'No Institutional Holdings for this security' in html:
            raise LookupError('No Institutional Holdings for this security')

        lines = lines[f('START Left-column') + 1:f('END left-column')]

        self.ownership_holding_pct = float(c(lines[f('Institutional Ownership') + 1])[:-1])

        self.ownership_buy_count = int(c(lines[f('Increased Positions') + 1]))
        self.ownership_buy_share = long(c(lines[f('Increased Positions') + 2]))
        self.ownership_held_count = int(c(lines[f('Held Positions') + 1]))
        self.ownership_held_share = long(c(lines[f('Held Positions') + 2]))
        self.ownership_sell_count = int(c(lines[f('Decreased Positions') + 1]))
        self.ownership_sell_share = long(c(lines[f('Decreased Positions') + 2]))

        self.ownership_na = self.ownership_buy_share - self.ownership_sell_share
        self.ownership_na_pct = round(self.ownership_na / float(
            self.ownership_held_share - self.ownership_buy_share + self.ownership_sell_count  # before change
        ) * 100, 2)

        self.ownership_new_count = int(c(lines[f('New Positions') + 1]))
        self.ownership_new_share = int(c(lines[f('New Positions') + 2]))
        self.ownership_out_count = int(c(lines[f('Sold Out Positions') + 1]))
        self.ownership_out_share = int(c(lines[f('Sold Out Positions') + 2]))

        # Owner Name
        top15 = ''.join(lines[f('Owner Name') - 4:f('<!--end genTable-->') - 5])
        top15 = top15.replace('&amp;', '').replace('&', '')

        class OwnershipParser(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self)

                self.counter = 0

                self.data = list()
                self.temp = list()

            def handle_data(self, data):
                data = data.strip()

                if data:
                    self.temp.append(data)
                    self.counter += 1

                    if self.counter > 5:
                        self.data.append(self.temp)
                        self.temp = list()
                        self.counter = 0

                return self

        parser = OwnershipParser()
        parser.feed(top15)

        # top 15
        self.ownership_top15_sum = 0
        self.ownership_top15_na_pct = 0
        for d in parser.data[1:]:
            #print d
            self.ownership_top15_sum += long(d[2].replace(',', ''))
            self.ownership_top15_na_pct += long(('-' + d[3][1:-1] if '(' == d[3][0] else d[3]).replace(',', ''))
        else:
            self.ownership_top15_na_pct = round(self.ownership_top15_na_pct / float(self.ownership_top15_sum) * 100, 2)

        return self

    def get_insider(self):
        """
        Get insider trade data from nasdaq
        """
        # first get institute holding
        response = urlopen(
            'http://www.nasdaq.com/symbol/{symbol}/insider-trades'.format(
                symbol=self.symbol.lower()
            )
        )
        html = response.read()

        lines = html.split('\r\n')
        # html = open(r'C:\Users\Jack\Downloads\222.html').read()
        #lines = html.split('\n')

        f = lambda x: lines.index([l for l in lines if x in l].pop())
        c = lambda x: x[x.index('>') + 1:x.rindex('<')].replace(',', '')

        if 'There are no insiders for this security' in html:
            raise LookupError('There are no insiders for this security')

        lines = lines[f('START Left-column') + 1:f('END left-column')]

        self.insider_buy_3m = int(c(lines[f('# of Open Market Buys') + 1]))
        self.insider_buy_12m = int(c(lines[f('# of Open Market Buys') + 2]))
        self.insider_sell_3m = int(c(lines[f('# of Sells') + 1]))
        self.insider_sell_12m = int(c(lines[f('# of Sells') + 2]))

        self.insider_buy_share_3m = long(c(lines[f('# of Shares Bought') + 1]))
        self.insider_buy_share_12m = long(c(lines[f('# of Shares Bought') + 2]))
        self.insider_sell_share_3m = long(c(lines[f('# of Shares Sold') + 1]))
        self.insider_sell_share_12m = long(c(lines[f('# of Shares Sold') + 2]))

        self.insider_na_3m = self.insider_buy_share_3m - self.insider_sell_share_3m
        self.insider_na_12m = self.insider_buy_share_12m - self.insider_sell_share_12m

        return self

    def get_short_interest(self):
        """
        Get short interest from:
        http://www.nasdaq.com/symbol/aapl/short-interest
        and make it dataframe
        """
        # first get institute holding
        response = urlopen(
            'http://www.nasdaq.com/symbol/{symbol}/short-interest'.format(
                symbol=self.symbol.lower()
            )
        )
        html = response.read()
        lines = html.split('\r\n')
        # html = open(r'C:\Users\Jack\Downloads\333.html').read()
        #lines = html.split('\n')

        if 'No Short Interest' in html:
            raise LookupError('No Short Interest')

        f = lambda x: lines.index([l for l in lines if x in l].pop())

        lines = lines[f('Settlement Date') - 3:f('floatL marginL25px') - 3]

        class ShortInterestParser(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self)

                self.counter = 0

                self.data = list()
                self.temp = list()

            def handle_data(self, data):
                data = data.strip()

                if data:
                    self.temp.append(data)
                    self.counter += 1

                    if self.counter > 3:
                        self.data.append(self.temp)
                        self.temp = list()
                        self.counter = 0

                return self

        parser = ShortInterestParser()
        parser.feed(''.join(lines))

        short_interests = {
            'date': list(),
            'short_interest': list(),
            'avg_volume': list(),
            'day_to_cover': list()
        }
        for d in parser.data[1:]:
            short_interests['date'].append(pd.datetime.strptime(d[0], '%m/%d/%Y').date())
            short_interests['short_interest'].append(long(d[1].replace(',', '')))
            short_interests['avg_volume'].append(long(d[2].replace(',', '')))
            short_interests['day_to_cover'].append(float(d[3]))

        self.df_short_interest = pd.DataFrame(short_interests).to_csv()

        return self

    def get_rating(self):
        """
        Get analyst brokerage rating from zack:
        http://www.zacks.com/stock/research/DDD/brokerage-recommendations
        """
        # first get institute holding
        response = urlopen(
            'http://www.zacks.com/stock/research/{symbol}/brokerage-recommendations'.format(
                symbol=self.symbol.upper()
            )
        )
        html = response.read()
        lines = html.split('\n')
        #print html
        #html = open(r'C:\Users\Jack\Downloads\444.html').read()
        #lines = html.split('\n')

        f = lambda x: lines.index([l for l in lines if x in l].pop())
        c = lambda x: x[x.index('>') + 1:x.rindex('<')].replace(',', '')

        # Current ABR
        self.abr_current = float(c(c(lines[f('Current ABR') + 1])))
        self.abr_previous = float(c(c(lines[f('ABR (Last week)') + 1])))
        self.abr_rating_count = int(c(c(lines[f('# of Recs in ABR') + 1])))
        self.abr_target = float(c(c(lines[f('Average Target Price') + 1])).replace('$', ''))

        return self

























