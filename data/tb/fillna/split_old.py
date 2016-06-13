import os
from fractions import Fraction

from data.models import SplitHistory, Underlying
from data.tb.clean import get_quote_data
from data.tb.fillna.calc import *
from rivers.settings import CLEAN_DIR

output = '%-6s | %-30s'


class FillNaSplitOld(object):
    def __init__(self, symbol):
        self.symbol = symbol.lower()
        self.df_stock = pd.DataFrame()

        self.df_split0 = pd.DataFrame()
        self.df_rate = pd.DataFrame()
        self.df_div = pd.DataFrame()

        self.df_missing = pd.DataFrame()
        self.df_fillna = pd.DataFrame()

        self.split_history = []
        self.path = os.path.join(CLEAN_DIR, '__%s__.h5' % self.symbol)

    def get_data(self):
        """
        Prepare data from fill missing row
        """
        df_div, df_rate, df_stock = get_quote_data(self.symbol)

        db = pd.HDFStore(self.path)
        df_split0 = db.select('option/clean/split/old')
        df_split0 = df_split0.reset_index(drop=True)
        db.close()

        print output % ('PROC', 'Prepare and merge data')
        self.df_stock = df_stock.set_index('date')['close']
        self.df_rate = df_rate.set_index('date')['rate']
        self.df_div = df_div
        self.df_split0 = df_split0

        # get split history, error if not exists
        self.split_history = SplitHistory.objects.filter(symbol=self.symbol.upper())
        if not self.split_history.exists():
            raise LookupError('No split history found')

        # update stock price
        for split_history in self.split_history:
            self.df_stock.iloc[
                self.df_stock.index >= pd.to_datetime(split_history.date)
            ] *= Fraction(split_history.fraction)

        # output stat
        print output % ('STAT', 'Length df_split/old: %d' % len(df_split0))
        print output % ('STAT', 'Split history: %s' % self.split_history)

    def count_missing(self):
        """
        Count every option_code missing in df_split/old using df_stock dates
        """
        print '-' * 70
        print output % ('PROC', 'Count option_code missing')
        print '-' * 70
        # using groupby method
        df = self.df_split0.copy()
        """:type: pd.DataFrame"""

        df_stock = self.df_stock.copy()
        """:type: pd.DataFrame"""

        group = df.groupby('option_code')

        # all option_code missing stat
        df_stat = pd.DataFrame({
            'count0': group['date'].count(),
            'start': group['date'].min(),
            'stop': group['date'].max()
        })
        print output % ('STAT', 'Total df_stat length: %d' % len(df_stat))

        df_stat['count1'] = df_stat.apply(
            lambda s: len(df_stock.ix[s['start']:s['stop']]),
            axis=1
        )

        df_stat['missing'] = df_stat['count0'] != df_stat['count1']

        # get missing
        df_missing = df_stat[df_stat['missing']].reset_index()
        print output % ('STAT', 'Total missing length: %d' % len(df_missing))
        df_missing['diff'] = df_missing['count1'] - df_missing['count0']
        df_missing['pct'] = df_missing['count0'] / df_missing['count1']
        df_missing['fill0'] = df_missing['pct'] >= 0.75
        df_missing['fill1'] = (
            ((df_missing['diff'] < 6) & (df_missing['count0'] > 1)) |
            (df_missing['diff'] < 21)
        )
        df_missing['fill'] = df_missing['fill0'] | df_missing['fill1']
        print output % ('STAT', 'Total fillna length: %d' % len(df_missing[df_missing['fill']]))

        # print df_missing[df_missing['fill']].to_string(line_width=1000)
        # print df_missing[~df_missing['fill']].to_string(line_width=1000)
        self.df_missing = df_missing.copy()

    def fill_missing(self):
        """
        Fill missing rows
        """
        print '-' * 70
        print output % ('PROC', 'Start fill missing rows')
        print '-' * 70
        df_data = self.df_split0[self.df_split0['option_code'].isin(self.df_missing['option_code'])]
        df_missing = self.df_missing[self.df_missing['fill']].copy()

        new = []
        for _, data in df_missing.iterrows():
            print output % ('CODE', 'Missing option_code: %s' % data['option_code'])
            print '-' * 70
            df = df_data.query('option_code == %r' % data['option_code']).reset_index(drop=True)
            df = df.sort_values('date', ascending=True)
            # print df.to_string(line_width=1000)

            ex_date = df['ex_date'].iloc[0].strftime('%y%m%d')
            name = 1 if df['name'].iloc[0] == 'CALL' else -1
            strike = df['strike'].iloc[0]

            # find nearby index
            stock_dates = pd.Series(self.df_stock.ix[df['date'].min():df['date'].max()].index)
            missing_dates = stock_dates[~stock_dates.isin(df['date'])]

            for date in missing_dates:
                date_str = date.strftime('%y%m%d')
                print output % ('DATE', 'missing: %s, ex_date: %s, name: %s, strike: %s' % (
                    date_str, ex_date, name, strike
                ))

                # get nearby rows
                idx = (np.abs(stock_dates - date)).argmin()
                ids = [i for i in range(idx - 2, idx + 3) if 0 <= i < len(df)]
                nearby = stock_dates[stock_dates.index.isin(ids)]
                df_current = df[df['date'].isin(nearby)]

                if len(df_current):
                    # noinspection PyUnresolvedReferences
                    mean = {
                        'bid': round((1 - (df_current['bid'] / df_current['theo_price'])).mean(), 2),
                        'ask': round(((df_current['ask'] / df_current['theo_price']) - 1).mean(), 2),
                        'impl_vol': round(df_current['impl_vol'].mean(), 2),
                    }
                    print output % ('FIND', 'Use nearby data, length: %d' % len(df_current))
                else:
                    print output % ('SKIP', 'No nearby date exist')
                    continue

                clean = OptionCalc(
                    ex_date,
                    name,
                    strike,
                    date_str,
                    round(self.df_rate[date], 4),
                    round(self.df_stock[date], 4),
                    0.0,
                    0.0,
                    mean['impl_vol'],
                    0.0  # later
                )

                theo_price = clean.theo_price() + 0
                if theo_price == 0 or np.isnan(mean['bid']) or np.isnan(mean['ask']):
                    bid = 0
                    ask = 0
                else:
                    bid = round(theo_price * (1 - mean['bid']), 2)
                    ask = round(theo_price * (1 + mean['ask']), 2)

                    if bid == ask:
                        ask += 0.01

                clean.bid = bid
                clean.ask = ask
                intrinsic, extrinsic = clean.moneyness()
                dte = clean.dte()
                prob_itm, prob_otm, prob_touch = clean.prob()
                delta, gamma, theta, vega = clean.greek()

                print output % (
                    'FILL', 'Date: %s, bid: %.2f, ask: %.2f,' % (date.strftime('%Y-%m-%d'), bid, ask)
                )

                contract = df_current.iloc[0][[
                    # 'ex_month', 'ex_year',
                    'ex_date', 'name','option_code', 'others', 'right', 'special', 'strike'
                ]]
                result = {
                    'date': date,
                    # 'close': round(df_stock[date], 2),
                    'option_code': contract['option_code'],
                    'impl_vol': mean['impl_vol'],
                    'theo_price': theo_price,
                    'bid': bid,
                    'ask': ask,
                    'intrinsic': intrinsic + 0,
                    'extrinsic': extrinsic + 0,
                    'dte': dte,
                    'prob_itm': prob_itm,
                    'prob_otm': prob_otm,
                    'prob_touch': prob_touch,
                    'delta': delta,
                    'gamma': gamma,
                    'theta': theta,
                    'vega': vega,
                    'last': 0.0,
                    'mark': round((bid + ask) / 2.0, 2),
                    'open_int': np.nan,
                    'volume': np.nan,
                    'ex_date': contract['ex_date'],
                    # 'ex_month': contract['ex_month'],
                    # 'ex_year': contract['ex_year'],
                    'name': contract['name'],
                    'others': contract['others'],
                    'special': contract['special'],
                    'right': contract['right'],
                    'strike': contract['strike']
                }

                # update current rows
                df = pd.concat([df, pd.DataFrame([result])])

            # fill volume and open interest
            df = df.sort_values('date')
            df['open_int'] = df['open_int'].fillna(method='pad')
            df['volume2'] = np.abs(df['open_int'] - df['open_int'].shift(1))
            df['volume'] = df.apply(
                lambda d: d['volume2'] if np.isnan(d['volume']) else d['volume'],
                axis=1
            )

            df['volume'] = np.abs(df['volume'])
            # print df.to_string(line_width=1000)
            del df['volume2']

            # only append missing dates
            df = df[df['date'].isin(missing_dates)]
            new.append(df)

            print '-' * 70

        if len(new):
            # make df
            df_fillna = pd.concat(new)
            """:type: pd.DataFrame"""
            for key in ('prob_itm', 'prob_otm', 'prob_touch', 'impl_vol'):
                df_fillna[key] = np.round(df_fillna[key], 2)
            # print df_fillna.to_string(line_width=1000)

            self.df_fillna = df_fillna.copy()

            print output % ('STAT', 'Complete fill missing, new rows: %d' % len(df_fillna))

    def remove_missing(self):
        """
        Remove the all rows is too many missing
        """
        print '-' * 70
        print output % ('PROC', 'Remove absence rows')
        print '-' * 70
        df_remove = self.df_missing[~self.df_missing['fill']].copy()
        remove_codes = df_remove['option_code']

        df_split0 = self.df_split0.copy()
        """:type: pd.DataFrame"""
        length0 = len(df_split0)
        print output % ('STAT', 'Length df_split/old before remove: %d' % length0)
        df_split0 = df_split0[~df_split0['option_code'].isin(remove_codes)]
        print output % ('STAT', 'Length df_split/old after remove: %d' % len(df_split0))
        print output % ('STAT', 'Total remove: %d' % (length0 - len(df_split0)))
        self.df_split0 = df_split0.copy()

    def save(self):
        """
        Process all fillna method then save data
        """
        self.get_data()
        self.count_missing()
        self.fill_missing()
        self.remove_missing()

        print '-' * 70
        print output % ('SAVE', 'Save df_split/old with fillna data')
        print '-' * 70

        df_split0 = pd.concat([self.df_split0, self.df_fillna])
        """:type: pd.DataFrame"""

        db = pd.HDFStore(self.path)
        try:
            db.remove('option/fillna/split/old')
        except KeyError:
            pass
        db.append('option/fillna/split/old', df_split0)
        db.close()

    def update_underlying(self):
        """
        Update underlying after completed
        """
        df_split0 = pd.concat([self.df_split0, self.df_fillna])
        """:type: pd.DataFrame"""

        underlying = Underlying.objects.get(symbol=self.symbol.upper())
        underlying.log += 'Fillna clean normal option: %s\n' % self.symbol.upper()
        underlying.log += 'Total new rows fill: %d\n' % len(self.df_fillna)
        underlying.log += 'Fillna df_split/old length: %d\n' % len(df_split0)
        underlying.save()
