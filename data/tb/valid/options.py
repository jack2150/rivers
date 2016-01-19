import pandas as pd

from data.models import Underlying
from rivers.settings import QUOTE


output = '%-6s | %-30s'


class ValidOption(object):
    def __init__(self, symbol):
        self.symbol = symbol.lower()
        self.df_list = {}

    @staticmethod
    def bid_gt_ask(df):
        """
        Bid is greater than ask price, data is wrong
        :param df: pd.DataFrame
        """
        print '=' * 70
        print 'Valid bid > ask'
        print '=' * 70
        df_error = df.query('bid >= ask').copy()
        remove = []

        for index, (bid, ask, last) in df_error[['bid', 'ask', 'last']].iterrows():
            gap = bid - ask
            print output % ('VALID', 'Error: bid >= ask, %s >= %s, last: %s' % (bid, ask, last))
            if ask == last:
                new_bid = ask - gap
                print output % ('FIX', 'Last same as ask, new_bid: %s' % new_bid)
                df.loc[df.index == index, 'bid'] = new_bid
            elif bid == last:
                new_ask = bid - gap
                print output % ('FIX', 'Last same as bid, new_ask: %s' % new_ask)
                df.loc[df.index == index, 'ask'] = new_ask
            elif bid == ask and (bid > 0 or ask > 0):
                # same bid ask, no idea to verify, remove
                remove.append(index)
            else:
                # if last is different either bid or ask, reverse both
                temp = ask
                ask = bid
                bid = temp
                print output % ('FIX', 'Reverse both bid & ask: %s -> %s, %s -> %s' % (
                    bid, ask, ask, bid
                ))
                df.loc[df.index == index, ['bid', 'ask']] = (bid, ask)

        # remove save big ask
        df = df[~df.index.isin(remove)]

        return df

    @staticmethod
    def ask_gt_1k(df):
        """
        Some have greater than 1000 bid ask price
        :param df: pd.DataFrame
        """
        print '=' * 70
        print 'Valid ask > 1000'
        print '=' * 70
        df_error = df.query('ask > 1000 | bid > 1000')

        for index, data in df_error.iterrows():
            print output % (
                'REMOVE', 'Invalid bid or ask (%s %s): %s, %s' % (
                    data['option_code'], data['date'].strftime('%Y-%m-%d'),
                    data['bid'], data['ask']
                )
            )
        if len(df_error):
            df = df[~df.index.isin(df_error.index)]

        return df

    @staticmethod
    def bid_zero_ask_gt_one(df):
        """
        Bid ask spread range is too large
        :param df: pd.DataFrame
        """
        print '=' * 70
        print 'Valid bid == 0 & ask > 1'
        print '=' * 70
        df_error = df.query('bid == 0 & ask > 1')
        for index, data in df_error.iterrows():
            print output % (
                'REMOVE', 'Bid ask gap too large (%s %s): %s, %s' % (
                    data['option_code'], data['date'].strftime('%Y-%m-%d'),
                    data['bid'], data['ask']
                )
            )
        if len(df_error):
            df = df[~df.index.isin(df_error.index)]

        return df

    @staticmethod
    def column_lt_zero(df):
        """
        All column should be not less than zero
        :param df: pd.DataFrame
        """
        print '=' * 70
        print 'Valid other columns'
        print '=' * 70

        df_error = df.query('ask < 0 & bid < 0 & volume < 0 & open_int < 0 & dte < 0')

        for index, data in df_error.iterrows():
            print output % (
                'REMOVE', 'Some columns is < 0 (%s %s): %s, %s' % (
                    data['option_code'], data['date'].strftime('%Y-%m-%d'),
                    data['bid'], data['ask']
                )
            )

        if len(df_error):
            df = df[~df.index.isin(df_error.index)]

        return df

    def start(self):
        """
        Start all validation
        """
        names = ['normal', 'others', 'split0', 'split1']
        keys = ['normal', 'others', 'split/old', 'split/new']
        db = pd.HDFStore(QUOTE)
        for name, key in zip(names, keys):
            try:
                self.df_list[name] = db.select('option/%s/raw/%s' % (self.symbol, key))
            except KeyError:
                pass
        db.close()
        
        df_result = {}
        for name, key in zip(names, keys):
            if name in self.df_list.keys():
                print 'Run valid for df_%s' % name
                self.df_list[name] = self.bid_gt_ask(self.df_list[name])
                self.df_list[name] = self.ask_gt_1k(self.df_list[name])
                self.df_list[name] = self.bid_zero_ask_gt_one(self.df_list[name])
                self.df_list[name] = self.column_lt_zero(self.df_list[name])

                # reset_index then save
                df_result[name] = self.df_list[name].reset_index(drop=True)
            else:
                df_result[name] = pd.DataFrame()
        
        db = pd.HDFStore(QUOTE)
        try:
            db.remove('option/%s/valid' % self.symbol)
        except KeyError:
            pass
        for name, key in zip(names, keys):
            if len(df_result[name]):
                db.append('option/%s/valid/%s' % (self.symbol, key), df_result[name])
        db.close()
        
        print 'All validation complete and save'

    def update_underlying(self):
        """
        Update underlying after completed
        """
        underlying = Underlying.objects.get(symbol=self.symbol.upper())
        names = ['normal', 'others', 'split0', 'split1']
        keys = ['normal', 'others', 'split/old', 'split/new']
        underlying.log += 'Valid Raw, symbol: %s\n' % self.symbol.upper()
        for name, key in zip(names, keys):
            if name in self.df_list.keys():
                underlying.log += 'Raw df_%s length: %d\n' % (key, len(self.df_list[name]))

        underlying.save()
