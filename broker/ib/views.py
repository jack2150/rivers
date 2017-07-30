import glob
import os
import logging
import numpy as np
import pandas as pd
import json
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, FloatField, Count
from django.db.models import Sum
from django.shortcuts import render, redirect
from pandas.tseries.offsets import Hour
from broker.ib.models import *
from rivers.settings import IB_STATEMENT_DIR, CSV_DIR

logger = logging.getLogger('views')


IB_NAMES = {
    'statement': (
        'stock_prior', 'stock_trans', 'stock_pl_mtm_prior', 'stock_pl_mtm_trans', 'stock_end',
        'option_prior', 'option_trans', 'option_pl_mtm_prior', 'option_pl_mtm_trans', 'option_end',
    ),
    'netassetvalue': (
        'asset', 'total', 'total_long', 'total_short', 'total_prior', 'total_change'
    ),
    'marktomarket': (
        'symbol', 'options', 'qty0', 'qty1', 'price0', 'price1',
        'pl_pos', 'pl_trans', 'pl_fee', 'pl_other', 'pl_total'
    ),
    'performance': (
        'symbol', 'cost_adj',
        'real_st_profit', 'real_st_loss', 'real_lt_profit', 'real_lt_loss', 'real_total',
        'unreal_st_profit', 'unreal_st_loss', 'unreal_lt_profit', 'unreal_lt_loss', 'unreal_total',
        'total'
    ),
    'profitloss': (
        'asset', 'symbol', 'options', 'option_code', 'company', 'pl_mtd', 'pl_ytd',
        'real_st_mtd', 'real_st_ytd', 'real_lt_mtd', 'real_lt_ytd'
    ),
    'cashreport': (
        'summary', 'currency', 'total', 'security', 'future', 'pl_mtd', 'pl_ytd'
    ),
    'openposition': (
        'side', 'asset', 'currency', 'symbol', 'qty', 'multiplier',
        'cost_price', 'cost_basic', 'close_price', 'total_value', 'unreal_pl', 'nav_pct'
    ),
    'positiontrade': (
        'order', 'asset', 'currency', 'symbol', 'date_time', 'exchange', 'qty',
        'trade_price', 'cost_price', 'proceed', 'fee', 'real_pl', 'mtm_pl'
    ),
    'financialinfo': (
        'options', 'asset', 'symbol', 'company', 'con_id',
        'sec_id', 'multiplier'
    ),
    'interestaccrual': (
        'currency', 'summary', 'interest',
    )
}

NAV_ASSETS = ('total', 'stock', 'options', 'cash')

IB_STATEMENT_NAME_CSV = 'ib_statement_name'
IB_STATEMENT_CSV = 'ib_statement'

IB_EXPORT_NAMES = {
    'nav': 'ib_nav.csv',
    'trade': 'ib_trade.csv',
    'mark': 'ib_mark.csv',
}


def ib_statement_import(request, obj_id):
    """
    Import IB statement single date
    :param obj_id: int
    :param request: request
    :return: redirect
    """
    ib_statement = IBStatement.objects.get(id=obj_id)

    for name in IB_NAMES.keys():
        if name == 'statement':
            continue

        obj_set = getattr(ib_statement, 'ib%s_set' % name)
        if obj_set.count():
            logger.info('%s remove ib%s_set %d' % (ib_statement, name, obj_set.count()))
            obj_set.all().delete()

    date_str = ib_statement.date.strftime('%Y%m%d')
    year = ib_statement.date.strftime('%Y')
    fname = '%s_%s_%s.csv' % (ib_statement.statement_name.account_id.upper(), date_str, date_str)
    ib_statement.statement_import(ib_statement.statement_name, year, fname, True)

    return redirect('admin:ib_ibstatement_changelist')


def ib_statement_imports(request, ib_path):
    """
    Import IB  statement import all in folder
    :param ib_path: str
    :param request: request
    :return: redirect
    """
    ib_statement_name = IBStatementName.objects.get(path=ib_path)

    folder_path = os.path.join(IB_STATEMENT_DIR, ib_statement_name.path)
    year_folders = glob.glob(os.path.join(folder_path, '*'))
    for year_folder in year_folders:
        year_files = glob.glob(os.path.join(year_folder, '*.csv'))
        year = os.path.basename(year_folder)

        for csv_file in year_files:
            fname = os.path.basename(csv_file)

            ib_statement = IBStatement()
            ib_statement.statement_import(ib_statement_name, year, fname)

    return redirect('admin:ib_ibstatement_changelist')


def ib_statement_truncate(request, obj_id):
    """
    Remove all ib statement and re-import
    :param request: request
    :param obj_id: id
    :return: render
    """
    ib_statement_name = IBStatementName.objects.get(id=obj_id)
    ib_statements = ib_statement_name.ibstatement_set.all()
    ib_positions = ib_statement_name.ibposition_set.all()
    logger.info('Remove IBStatements: %s' % len(ib_statements))
    logger.info('Remove IBPosition: %s' % len(ib_positions))
    ib_statements.delete()
    ib_positions.delete()

    return redirect('admin:ib_ibstatement_changelist')


def ib_statement_create_csv(request, obj_id):
    """
    Generate using third party data visual software
    A chart that show total nav & daily pl
    also show total in stock, options, cash in compare
    you make decision base on that
    buy more stock? buy more options? too many cash?
    :param request: request
    :param obj_id: int
    :return: render
    """
    ib_statement_name = IBStatementName.objects.get(id=obj_id)
    ib_statements = ib_statement_name.ibstatement_set.filter(
        date__range=[ib_statement_name.move_dist, ib_statement_name.stop]
    ).order_by('date')

    if len(ib_statements):
        nav_to_csv(ib_statements)
        trade_to_csv(ib_statements)
        mark_to_csv(ib_statements)

    return redirect('admin:ib_ibstatementname_changelist')


def nav_to_csv(ib_statements):
    """
    Answer question:
    Total NAV daily, weekly, monthly, mover
    change by stock, options, cash
    :param ib_statements:
    :return:
    """
    nav_names = []
    for asset in NAV_ASSETS:
        for name in IB_NAMES['netassetvalue']:
            if name == 'asset':
                continue

            key = '%s_%s' % (asset, name)
            nav_names.append(key)

    # start open file
    fpath = os.path.join(CSV_DIR, IB_STATEMENT_NAME_CSV, IB_EXPORT_NAMES['nav'])
    nav_file = open(fpath, mode='w')
    nav_file.write('id,date,%s\n' % ','.join(nav_names))
    # loop ib_statement
    for ib_statement in ib_statements:
        date = ib_statement.date.strftime('%Y-%m-%d')
        raw_id = ib_statement.date.strftime('%Y%m%d')

        # nav
        nav_raw = []
        for asset in NAV_ASSETS:
            try:
                ib_nav = ib_statement.ibnetassetvalue_set.get(asset=asset)
            except ObjectDoesNotExist:
                ib_nav = None

            for name in IB_NAMES['netassetvalue']:
                if name == 'asset':
                    continue

                # key = '%s_%s' % (asset, name)
                # print '%s,' % key,
                # print key, getattr(ib_nav, name)
                if ib_nav:
                    nav_raw.append('%.2f' % float(getattr(ib_nav, name)))
                else:
                    nav_raw.append('%.2f' % 0)

                    # nav_raw.append('')

        nav_file.write('%s,%s,%s\n' % (raw_id, date, ','.join(nav_raw)))

    logger.info('nav csv create: %s' % fpath)
    # close file
    nav_file.close()


def trade_to_csv(ib_statements):
    """
    IBMarkToMarket
    Answer question:
    how many order per day, y, how much fee total, and average per day, y
    stock trade & fee, options trade & fee
    how many symbol y, time order filled? exchange filled?
    time is wrong, just adjust -5 hours is done
    also, dte for order, pl by dte (new)
    enter or exit? profit or loss (stock vs options)

    :param ib_statements:
    :return:
    """
    nav_names = []
    for name in IB_NAMES['positiontrade']:
        nav_names.append(name)

    # start open file
    fpath = os.path.join(CSV_DIR, IB_STATEMENT_NAME_CSV, IB_EXPORT_NAMES['trade'])
    temp_file = open(fpath, mode='w')
    temp_file.write('id,date,%s,fill,pl,dte\n' % ','.join(nav_names))

    # loop ib_statement
    for ib_statement in ib_statements:
        date = ib_statement.date.strftime('%Y-%m-%d')
        raw_id = ib_statement.date.strftime('%Y%m%d')

        # position trades
        trades = ib_statement.ibpositiontrade_set.all()

        if len(trades):
            for trade in trades:
                trade = trade
                """:type: IBPositionTrade"""
                raw = []
                for name in IB_NAMES['positiontrade']:
                    # print name, getattr(order, name)
                    if name == 'date_time':
                        dt = getattr(trade, name) - Hour(5)
                        raw.append('"%s"' % dt.strftime('%Y-%m-%d %H:%M'))
                    else:
                        try:
                            temp = '%.2f' % float(getattr(trade, name))
                        except ValueError:
                            temp = '%s' % getattr(trade, name).capitalize()
                            if name in ('currency', 'symbol'):
                                temp = '%s' % getattr(trade, name).upper()

                        raw.append(temp)

                if trade.mtm_pl != 0:
                    raw.append('Exit')

                    if trade.mtm_pl > 0:
                        raw.append('Profit')
                    else:
                        raw.append('Loss')
                else:
                    raw.append('Enter')
                    raw.append('Even')

                # add dte
                if trade.options:
                    raw.append('%d' % (trade.ex_date.date() - ib_statement.date).days)
                else:
                    raw.append('0')

                temp_file.write('%s,%s,%s\n' % (raw_id, date, ','.join(raw)))

    logger.info('trade csv create: %s' % fpath)
    # close file
    temp_file.close()


def mark_to_csv(ib_statements):
    """
    Answer question:
    What you holding? stock vs options? Holding is p or l?
    Daily p/l, Daily p/l by stocks vs options.
    :param ib_statements: IBStatement
    """
    # start open file
    fpath = os.path.join(CSV_DIR, IB_STATEMENT_NAME_CSV, IB_EXPORT_NAMES['mark'])
    temp_file = open(fpath, mode='w')
    temp_file.write('id,date,%s,pl\n' % ','.join(IB_NAMES['marktomarket']))
    # loop ib_statement
    for ib_statement in ib_statements:
        ib_statement = ib_statement
        """:type: IBStatement """
        date = ib_statement.date.strftime('%Y-%m-%d')
        raw_id = ib_statement.date.strftime('%Y%m%d')

        marks = ib_statement.ibmarktomarket_set.all()

        for mark in marks:
            raw = []

            for name in IB_NAMES['marktomarket']:
                if name == 'symbol':
                    raw.append(getattr(mark, name))
                elif name == 'options':
                    raw.append('Options' if getattr(mark, name) else 'Stocks')
                else:
                    raw.append('%.2f' % getattr(mark, name))

            if mark.pl_total > 0:
                raw.append('Profit')
            elif mark.pl_total < 0:
                raw.append('Loss')
            else:
                raw.append('Even')

            temp_file.write('%s,%s,%s\n' % (raw_id, date, ','.join(raw)))

    logger.info('mark csv create: %s' % fpath)
    # close file
    temp_file.close()


def ib_statement_csv_symbol(request, obj_id):
    """
    Format:
    Ticker,Dollar Amount
    PTTAX,50000
    AAPL,15000
    Create csv file for morningstar x-ray
    :param request: request
    :param obj_id: int
    :return: render
    """
    ib_statement = IBStatement.objects.get(id=obj_id)

    # stock only
    fname_stock = 'mark_stock_%s.csv' % ib_statement.date.strftime('%Y%m%d')
    fpath_stock = os.path.join(CSV_DIR, IB_STATEMENT_CSV, fname_stock)
    stock_file = open(fpath_stock, mode='w')
    stock_file.write('Ticker,Dollar Amount\n')

    # options only
    fname_option = 'mark_option_%s.csv' % ib_statement.date.strftime('%Y%m%d')
    fpath_option = os.path.join(CSV_DIR, IB_STATEMENT_CSV, fname_option)
    option_file = open(fpath_option, mode='w')
    option_file.write('Ticker,Dollar Amount\n')

    # loop mark to market
    marks = ib_statement.ibmarktomarket_set.all()
    for mark in marks:
        total = mark.price1 * mark.qty1
        if mark.options:
            total *= 100
            option_file.write('%s,%.2f\n' % (mark.symbol, total))
        else:
            stock_file.write('%s,%.2f\n' % (mark.symbol, total))

    logger.info('Create csv for IBStatement %s holding symbols' % (
        ib_statement.date
    ))

    stock_file.close()
    option_file.close()

    return redirect('admin:ib_ibstatement_changelist')


def ib_position_create(request, obj_id):
    """
    View for IBPosition create
    :param request: request
    :param obj_id: int
    :return: render
    """
    ib_pos_create = IBPositionCreate(
        obj_id=obj_id
    )
    ib_pos_create.ready()
    ib_pos_create.create()

    return redirect('admin:ib_ibposition_changelist')


def ib_position_remove(request, obj_id):
    """
    View for IBPosition create
    :param request: request
    :param obj_id: int
    :return: render
    """
    ib_pos_create = IBPositionCreate(
        obj_id=obj_id
    )
    ib_pos_create.remove_related()
    ib_pos_create.remove_pos()

    return redirect('admin:ib_ibposition_changelist')


class IBPositionCreate(object):
    def __init__(self, obj_id):
        self.ib_statement_name = IBStatementName.objects.get(id=obj_id)
        self.ib_statements = self.ib_statement_name.ibstatement_set.order_by('date').all()

    def remove_related(self):
        """

        :return:
        """
        for ib_statement in self.ib_statements:
            ib_statement.ibpositiontrade_set.update(position=None)
            ib_statement.ibopenposition_set.update(position=None)
            ib_statement.ibmarktomarket_set.update(position=None)
            ib_statement.ibperformance_set.update(position=None)
            ib_statement.ibprofitloss_set.update(position=None)
            ib_statement.ibfinancialinfo_set.update(position=None)
            logger.info('%s pos related removed' % ib_statement)

    def remove_pos(self):
        """

        :return:
        """
        positions = self.ib_statement_name.ibposition_set.all()
        logger.info('IBPosition %d pos removed' % positions.count())
        positions.delete()

    def ready(self):
        """
        Remove all previous relation
        """
        # ib title
        IBPositionTrade.objects.filter(
            statement__statement_name=self.ib_statement_name
        ).update(position=None)
        IBOpenPosition.objects.filter(
            statement__statement_name=self.ib_statement_name
        ).update(position=None)
        IBMarkToMarket.objects.filter(
            statement__statement_name=self.ib_statement_name
        ).update(position=None)
        IBPerformance.objects.filter(
            statement__statement_name=self.ib_statement_name
        ).update(position=None)
        IBProfitLoss.objects.filter(
            statement__statement_name=self.ib_statement_name
        ).update(position=None)
        IBFinancialInfo.objects.filter(
            statement__statement_name=self.ib_statement_name
        ).update(position=None)

        # position
        IBPosition.objects.filter(
            statement_name=self.ib_statement_name
        ).delete()

    def create(self):
        """
        Create positions using IBStatement data, weekly
        """
        for ib_statement in self.ib_statements:
            pos_open = IBPosition.objects.filter(status='open')

            logger.info('IBStatement %s, pos_open: %d' % (ib_statement.date, pos_open.count()))
            self.pos_trade(ib_statement)
            self.pos_hold(ib_statement)

            # not exist or all obj must relate to pos
            assert not ib_statement.ibpositiontrade_set.filter(position__isnull=True).exists()
            assert not ib_statement.ibopenposition_set.filter(position__isnull=True).exists()
            assert not ib_statement.ibmarktomarket_set.filter(position__isnull=True).exists()
            assert not ib_statement.ibperformance_set.filter(position__isnull=True).exists()
            assert not ib_statement.ibfinancialinfo_set.filter(position__isnull=True).exists()
            # pl without hold also exists

    def pos_trade(self, ib_statement):
        """
        Position open & close & expire
        :param ib_statement: IBStatement
        """
        pos_open = IBPosition.objects.filter(status='open')

        ib_trades = ib_statement.ibpositiontrade_set
        ib_opens = ib_statement.ibopenposition_set
        ib_trade_orders = ib_trades.filter(order='Order')
        symbols = [s[0] for s in ib_trade_orders.values_list('symbol').distinct()]

        for symbol in symbols:
            orders = ib_trade_orders.filter(symbol=symbol)
            holds = ib_opens.filter(symbol=symbol)

            # print symbol, orders.count(), holds.count()

            if holds.count() == 0:
                try:
                    # closed or expire
                    order = orders.first()
                    """:type: IBPositionTrade """

                    status = 'close'
                    if ib_statement.date == order.ex_date:
                        # expire got no commission, and date is same as date

                        fee = orders.aggregate(Sum('fee'))['fee__sum']
                        # print ib_statement.date, order.ex_date, fee, fee == 0.0

                        if fee == 0:
                            status = 'expire'

                    pos = pos_open.get(symbol=symbol)

                    # update
                    pos.date1 = ib_statement.date
                    pos.status = status
                    pos.save()

                except ObjectDoesNotExist:
                    # day trade
                    pos = IBPosition(
                        statement_name=self.ib_statement_name,
                        symbol=symbol,
                        date0=ib_statement.date,
                        date1=ib_statement.date,
                        status='close'
                    )
                    pos.save()

                logger.info('Set: %s' % pos)
            else:
                # create new or use exists
                try:
                    pos = pos_open.get(symbol=symbol)
                except ObjectDoesNotExist:
                    pos = IBPosition(
                        statement_name=self.ib_statement_name,
                        symbol=symbol,
                        date0=ib_statement.date,
                        status='open'
                    )
                    pos.save()

                logger.info('New: %s' % pos)

            # add relation
            self.add_related(ib_statement, pos)

            # update
            trades = pos.ibpositiontrade_set.filter(order='Trade')
            pos.fee = trades.aggregate(fee=Sum('fee'))['fee']
            if trades.filter(options=True).exists():
                pos.options = True

            if pos.date1:
                pos.total = trades.aggregate(
                    total=Sum(F('qty') * F('cost_price'), output_field=FloatField())
                )['total'] * -1

                if pos.options:
                    pos.total *= 100  # for options

                if pos.total > 0:
                    pos.perform = 'profit'
                elif pos.total < 0:
                    pos.perform = 'loss'
                else:
                    pos.perform = 'even'

            pos.save()

    def pos_hold(self, ib_statement):
        """
        Position hold add relation
        :param ib_statement: IBStatement
        """
        pos_open = IBPosition.objects.filter(status='open')

        ib_trades = ib_statement.ibpositiontrade_set
        ib_opens = ib_statement.ibopenposition_set

        # unique symbols
        symbols0 = [s[0] for s in ib_opens.values_list('symbol').distinct()]
        symbols1 = [s[0] for s in pos_open.values_list('symbol').distinct()]

        for symbol in symbols0:
            # print symbol, 'hold', symbol in symbols1

            if symbol not in symbols1:
                raise LookupError('Hold positions is not opened: %s' % symbol)

            # only for no trade pos, trade already add
            if ib_trades.filter(symbol=symbol).count() == 0:
                # add relation
                pos = pos_open.get(symbol=symbol)
                logger.info('Hold: %s' % pos)
                self.add_related(ib_statement, pos)

    @staticmethod
    def add_related(ib_statement, pos):
        """
        Add relation to pos
        :param ib_statement: IBStatement
        :param pos: IBPosition
        """
        ib_statement.ibpositiontrade_set.filter(symbol=pos.symbol).update(position=pos)
        ib_statement.ibopenposition_set.filter(symbol=pos.symbol).update(position=pos)
        ib_statement.ibmarktomarket_set.filter(symbol=pos.symbol).update(position=pos)
        ib_statement.ibperformance_set.filter(symbol=pos.symbol).update(position=pos)
        ib_statement.ibprofitloss_set.filter(symbol=pos.symbol).update(position=pos)
        ib_statement.ibfinancialinfo_set.filter(symbol=pos.symbol).update(position=pos)


def get_ib_pos_data(ib_pos):
    """
    Get IBPosition related data and make a dataframe
    :param ib_pos: IBPosition
    :return: pd.DataFrame
    """
    order_data = {'perform': [], 'mark': [], 'pl': []}
    # openposition duplicate as perform
    ib_performs = ib_pos.ibperformance_set.order_by('statement__date')
    for temp in ib_performs.values('statement__date').annotate(total=Sum('total')):
        # print temp['statement__date'], temp['total']
        order_data['perform'].append({
            'date': temp['statement__date'],
            'perform': temp['total'],
        })
    ib_marks = ib_pos.ibmarktomarket_set.order_by('statement__date')
    for temp in ib_marks.values('statement__date').annotate(total=Sum('pl_total')):
        # print temp['statement__date'], temp['total']
        order_data['mark'].append({
            'date': temp['statement__date'],
            'mark': temp['total'],
        })

    # just monthly statement
    # for temp in ib_pos.ibprofitloss_set.all():
    #   print temp
    # orders = ib_pos.ibpositiontrade_set.filter(order='Order')
    # for temp in orders.order_by('statement__date').all():
    #     print temp
    # print pd.Series(data['pl'].items())
    df_perform = pd.DataFrame(order_data['perform']).set_index('date')
    df_mark = pd.DataFrame(order_data['mark']).set_index('date')
    df_data = pd.concat([df_perform, df_mark], axis=1)
    """:type: pd.DataFrame"""
    return df_data


def ib_position_report(request, obj_id):
    """
    View for IBPosition create
    :param request: request
    :param obj_id: int
    :return: render
    """
    ib_pos = IBPosition.objects.get(id=obj_id)
    df_data = get_ib_pos_data(ib_pos)

    # make it json
    json_raw = []
    for index, data in df_data.iterrows():
        temp = {key: float(value) for key, value in dict(data).items()}
        temp['date'] = index.strftime('%Y-%m-%d')

        temp['weekday'] = index.strftime('%w')

        if temp['perform'] > 0:
            temp['pos'] = 'profit'
        elif temp['perform'] < 0:
            temp['pos'] = 'loss'
        else:
            temp['pos'] = 'even'

        if temp['mark'] > 0:
            temp['move'] = 'increase'
        elif temp['mark'] < 0:
            temp['move'] = 'decrease'
        else:
            temp['move'] = 'no_change'

        json_raw.append(temp)

    json_data = json.dumps(json_raw)

    # entry/exit price
    order_data = []
    orders = ib_pos.ibpositiontrade_set.filter(order='Order').order_by('statement__date')
    trades = ib_pos.ibpositiontrade_set.filter(order='Trade').order_by('statement__date')
    for temp in orders.values('statement__date').distinct():
        date = temp['statement__date']

        total = 0
        date_orders = orders.filter(statement__date=date)
        for date_order in date_orders:
            # print date_order
            total += date_order.qty * date_order.cost_price

        order_data.append({
            'date': date,
            'orders': date_orders,
            'total': total
        })

    trade_total = sum([o['total'] for o in order_data]) * -1

    # every option have ex_date, strike,
    # every strike possible
    # final or not total pl
    if ib_pos.status == 'open':
        pl_total = df_data['perform'][-1]
    else:
        pl_total = trades.aggregate(
            total=Sum(F('qty') * F('cost_price'), output_field=FloatField())
        )['total'] * -1

        if trades.aggregate(Count('options')):
            # is options
            pl_total *= 100

    # print fee, qty, pl_total
    stat_data = {
        'fee': {
            'stock': 0,
            'option': 0,
        },
        'qty': {
            'stock': 0,
            'option': 0,
        },
        'period': 0,
        'pl_total': pl_total,
    }

    for t in trades:
        if t.options:
            stat_data['qty']['option'] += abs(t.qty)
            stat_data['fee']['option'] += t.fee
        else:
            stat_data['qty']['stock'] += abs(t.qty)
            stat_data['fee']['stock'] += t.fee

    if ib_pos.status == 'open':
        stat_data['period'] = (datetime.today().date() - ib_pos.date0).days
    else:
        stat_data['period'] = (ib_pos.date1 - ib_pos.date0).days

    print stat_data


    template = 'broker/ib/report.html'

    title = '{pos}: Report'.format(pos=ib_pos)
    parameters = dict(
        site_title=title,
        title=title,
        ib_pos=ib_pos,
        json_data=json_data,
        order_data=order_data,
        trade_total=trade_total,
        stat_data=stat_data,
    )

    return render(request, template, parameters)


# state management? on another view i guess
