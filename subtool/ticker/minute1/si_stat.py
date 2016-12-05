
class SiData(object):
    def __init__(self):
        pass



class SimpleIndicatorStat(object):
    def __init__(self, df_minute1, df_day):
        self.df_minute1 = df_minute1
        self.df_day = df_day

    def recent10days_mover(self):
        """
        distribute by up/down day for mover
        :return:
        """
        pass

    def bull_bear_count(self):
        """

        :return:
        """
        df = self.df_day.copy()
        df['pct_chg'] = df['close'].pct_change()

        total = 0
        mover = []
        for pct_chg in df['pct_chg']:
            if pct_chg > 0:
                total += 1
            elif pct_chg < 0:
                total -= 1

            mover.append(total)

        df['mover'] = mover

        df['min10'] = df['dt'].dt.minute % 10
        df['min30'] = df['dt'].dt.minute % 30

        df_min10 = df[df['min10'] == 0]
        df_min30 = df[df['min30'] == 0]
        print df_min10
        print df_min30

        # todo: no idea now, wait



        print {
            'max': df['mover'].max(),
            'min': df['mover'].min(),
            'median': df['mover'].median(),
            'std': round(df['mover'].std(), 2),
        }

        # todo: cont after eat

        return

    def volume_based(self):
        """

        :return:
        """
        pass