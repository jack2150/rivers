import logging
import os
import pandas as pd
from string import ascii_uppercase
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from rivers.settings import BASE_DIR
from statement.models import Statement, Position
from openpyxl import load_workbook
from openpyxl.styles import Font, Style
from subtool.live.excel_rtd.stat import ExcelRtdStatData

logger = logging.getLogger('views')
MAX_ROW = 500
# noinspection PyUnresolvedReferences
EXCEL_FILE = os.path.join(BASE_DIR, 'rtd.xlsx')
STOCK_NAMES = ('last', 'net_chg', 'volume', 'open', 'high', 'low')
STOCK_INDEX = ('A', 'C', 'I', 'J', 'K', 'L')
OPTION_ORDER = (
    'option_code', 'bid', 'mark', 'ask', 'last',
    'delta', 'gamma', 'theta', 'vega',
    'impl_vol', 'prob_itm', 'prob_otm', 'prob_touch',
    'volume', 'open_int', 'intrinsic', 'extrinsic',
)
HOLD_OPTION = (
    'option_code', 'contract', 'strike', 'exp', 'dte', 'qty',
    'trade_price', 'trade_value', 'close_price', 'close_value',
    'profit_loss_$', 'profit_loss_%'
)
CALL_NAMES = (
    'last', 'mark', 'delta', 'gamma', 'theta', 'vega', 'impl_vol', 'prob_itm', 'prob_otm',
    'prob_touch', 'volume', 'open_int', 'intrinsic', 'extrinsic', 'option_code', 'bid', 'bx',
    'ask', 'ax'
)
PUT_NAMES = (
    'bid', 'bx', 'ask', 'ax', 'last', 'mark', 'delta', 'gamma', 'theta', 'vega', 'impl_vol',
    'prob_itm', 'prob_otm', 'prob_touch', 'volume', 'open_int', 'intrinsic', 'extrinsic',
    'option_code',
)
STAGE_NAMES = (
    'price', 'lt_stage', 'lt_amount',
    'e_stage', 'e_amount', 'gt_stage', 'gt_amount'
)
CONDITION_NAMES = (
    'name', 'condition', 'profit_loss'
)
CLOSE_STAT = (
    'std_value', 'in_std', 'out_std', 'above_std', 'below_std',
    'close_gain', 'close_loss', '60_day_move'
)


def set_header(sheet, key, value):
    sheet[key] = value.replace('_', ' ').capitalize()
    sheet[key].style = Style(font=Font(bold=True))


def set_value(sheet, key, value):
    sheet[key] = str(value)


def set_int(sheet, key, value):
    sheet[key] = int(value)


def set_float(sheet, key, value):
    sheet[key] = value
    sheet[key].number_format = '0.00'


def set_percent(sheet, key, value):
    sheet[key] = value
    sheet[key].number_format = '0.00%'


def set_date(sheet, key, value):
    sheet[key] = value
    sheet[key].number_format = 'yy-mm-dd'


def make_close0_open1_expr(qcut_range, close_open):
    temp = [float(n) for n in qcut_range[1:-1].split(', ')]
    return temp[0], temp[1], '=AND(%s<=%s,%s<=%s)' % (
        temp[0], close_open, close_open, temp[1]
    )


def make_expr(cond, price):
    temp = cond.replace('x', 'value').replace('y', 'value')
    result = '%s' % temp.format(value=price).replace(' ', '').replace('==', '=')
    items = result.split('<')
    if len(items) == 3:
        result = '=AND(%s<%s, %s<%s)' % (items[0], items[1], items[1], items[2])
    else:
        result = '=%s' % result

    return result


def excel_rtd_create(request):
    """
    1. get all positions
    2. create a sheet in rtd.xlxs
    3. for every symbol
    3a. put symbol data into it
    3b. get data from other sheet
    3c. make calculation cell
    4. save and auto open file
    :param request: request
    :return: render
    """
    logger.info('create analysis sheet for excel rtd')
    wb = load_workbook(filename=EXCEL_FILE)
    sheets = wb.get_sheet_names()

    # get statement/holding data from db
    statement = Statement.objects.latest('date')
    positions = Position.objects.filter(status='OPEN').order_by('symbol')

    holding_equity = statement.holdingequity_set.all()
    holding_options = statement.holdingoption_set.all()

    symbols = [
        s[0] for s in holding_options.distinct('symbol').values_list('symbol')
    ]

    # calc stat data
    excel_stat = ExcelRtdStatData(symbols)
    excel_stat.get_data()
    stat_data = {}
    for symbol in symbols:
        logger.info('create sheet for symbol: %s' % symbol.upper())
        # if symbol not in ('AIG', 'BP'):
        #    print symbol
        #    continue

        df = excel_stat.df_all[symbol]
        vol5, vol20 = excel_stat.mean_vol(df)
        hl5, hl20 = excel_stat.hl_wide(df)
        stat_data[symbol] = {
            'close': excel_stat.latest_close(df),
            'mean_vol5': vol5,
            'mean_vol20': vol20,
            'mean_hl5': hl5,
            'mean_hl20': hl20,
            'oc_stat': excel_stat.open_move(df),
            'std_close': excel_stat.std_close(df),
        }

    # set excel cell
    for symbol in symbols:
        # if symbol not in ('AIG', 'BP'):
        #     continue

        sheet_name = '_%s' % symbol.upper()
        if sheet_name in sheets:
            ws0 = wb[sheet_name]
            wb.remove_sheet(ws0)
        ws0 = wb.create_sheet(0)
        ws0.title = sheet_name
        row = 1

        logger.info('Create for symbol: %s' % symbol)

        # select sheet
        if symbol.upper() not in sheets:
            continue
        ws1 = wb[symbol]

        set_header(ws0, 'A%d' % row, 'symbol')
        ws0['A%d' % (row + 1)] = symbol.upper()

        # create stock
        stock_price = 'B%d' % (row + 1)
        net_chg = 'K%d' % (row + 1)
        stock_volume = 'D%d' % (row + 1)
        close_open = 'J%d' % (row + 1)
        stock_open = 'E%d' % (row + 1)
        stock_high = 'F%d' % (row + 1)
        stock_low = 'G%d' % (row + 1)
        close_last = 'L%d' % (row + 1)

        for i, name in enumerate(STOCK_NAMES, start=1):
            set_header(ws0, '%s%d' % (ascii_uppercase[i], row), name)

            if name == 'volume':
                set_value(ws0, '%s%d' % (ascii_uppercase[i], row + 1), '=%s!%s' % (
                    symbol, '%s4' % STOCK_INDEX[i - 1]
                ))
            else:
                set_float(ws0, '%s%d' % (ascii_uppercase[i], row + 1), '=%s!%s' % (
                    symbol, '%s4' % STOCK_INDEX[i - 1]
                ))

        set_header(ws0, 'H%d' % row, 'prev_close')
        set_float(ws0, 'H%d' % (row + 1), stat_data[symbol]['close'])
        set_header(ws0, 'I%d' % row, 'c2_open_$')
        set_float(ws0, 'I%d' % (row + 1), '=H%d-E%d' % (row + 1, row + 1))
        set_header(ws0, 'J%d' % row, 'c2_open_%')
        set_percent(ws0, 'J%d' % (row + 1), '=I%d/H%d' % (row + 1, row + 1))
        set_header(ws0, 'K%d' % row, 'net_chg_%')
        set_percent(ws0, 'K%d' % (row + 1), '=C%d/E%d' % (row + 1, row + 1))
        set_header(ws0, 'L%d' % row, 'c2_last_%')
        set_percent(ws0, 'L%d' % (row + 1), '=1-B%d/H%d' % (row + 1, row + 1))

        row += 3

        # create options
        options = holding_options.filter(symbol=symbol)
        records = {}
        if options.count():
            for i, name in enumerate(OPTION_ORDER):
                set_header(ws0, '%s%d' % (ascii_uppercase[i], row), name)

            row += 1

        # get option codes
        call_codes = [c[0].value for c in ws1['Q1:Q%d' % ws1.get_highest_row()]]
        put_codes = [c[0].value for c in ws1['AP1:AP%d' % ws1.get_highest_row()]]

        for option in options:
            logger.info('Get option_code: %s' % option.option_code)
            if option.option_code in call_codes:
                index = call_codes.index(option.option_code) + 1
                raw = [
                    d.value for d in [c for c in ws1['C%d:U%d' % (index, index)]][0]
                ]
                data = {
                    k: v for k, v in zip(CALL_NAMES, raw)
                }

                for i, name in enumerate(OPTION_ORDER):
                    ws0['%s%d' % (ascii_uppercase[i], row)] = data[name]

                records[option.option_code] = data
                row += 1
            elif option.option_code in put_codes:
                index = put_codes.index(option.option_code) + 1
                raw = [
                    d.value for d in [c for c in ws1['X%d:AP%d' % (index, index)]][0]
                ]
                data = {
                    k: v for k, v in zip(PUT_NAMES, raw)
                }

                for i, name in enumerate(OPTION_ORDER):
                    if name in ('open_int', 'volume'):
                        set_value(ws0, '%s%d' % (ascii_uppercase[i], row), data[name])
                    else:
                        set_float(ws0, '%s%d' % (ascii_uppercase[i], row), data[name])

                records[option.option_code] = data
                row += 1

        row += 1

        # hold options
        if options.count():
            for i, name in enumerate(HOLD_OPTION):
                set_header(ws0, '%s%d' % (ascii_uppercase[i], row), name)
            set_header(ws0, 'M%d' % row, 'to_strike_$')
            set_header(ws0, 'N%d' % row, 'to_strike_%')
            row += 1

        for option in options:
            logger.info('Put option data into sheet: %s' % option.option_code)

            for i, name in enumerate(HOLD_OPTION):
                key = '%s%d' % (ascii_uppercase[i], row)

                if name == 'trade_value':  # G
                    set_float(ws0, key, '=F%d*G%d' % (row, row))
                elif name == 'close_price':  # H
                    set_float(ws0, key, records[option.option_code]['mark'])
                elif name == 'close_value':  # I
                    set_float(ws0, key, '=F%d*I%d' % (row, row))
                elif name == 'profit_loss_$':  # J
                    set_float(ws0, key, '=J%d-H%d' % (row, row))
                elif name == 'profit_loss_%':  # K
                    set_percent(ws0, key, '=K%d/H%d' % (row, row))
                elif name == 'qty':
                    set_int(ws0, key, getattr(option, name))
                elif name == 'exp':
                    ex_date = pd.to_datetime(getattr(option, name)).strftime('%Y-%m-%d')
                    set_date(ws0, key, ex_date)
                elif name == 'dte':
                    set_value(ws0, key, '=D%d-TODAY()' % row)
                else:
                    set_float(ws0, key, getattr(option, name))

            set_float(ws0, 'M%d' % row, '=%s-C%d' % (stock_price, row))
            set_percent(ws0, 'N%d' % row, '=%s/C%d-1' % (stock_price, row))

            row += 1

        set_float(ws0, 'F%d' % row, '=SUM(F%d:F%d)' % (row - options.count(), row - 1))
        set_float(ws0, 'G%d' % row, '=SUM(G%d:G%d)' % (row - options.count(), row - 1))
        set_float(ws0, 'H%d' % row, '=SUM(H%d:H%d)' % (row - options.count(), row - 1))
        close_value = 'I%d' % row
        set_float(ws0, close_value, '=SUM(I%d:I%d)' % (row - options.count(), row - 1))
        set_float(ws0, 'J%d' % row, '=SUM(J%d:J%d)' % (row - options.count(), row - 1))
        set_float(ws0, 'K%d' % row, '=SUM(K%d:K%d)' % (row - options.count(), row - 1))
        set_percent(ws0, 'L%d' % row, '=K%d/H%d' % (row, row))

        row += 2

        # stage section
        pos = positions.get(symbol=symbol)

        stages = pos.positionstage_set.all()

        if stages.count():
            for i, name in enumerate(STAGE_NAMES):
                set_header(ws0, '%s%d' % (ascii_uppercase[i], row), name)
            set_header(ws0, 'H%d' % row, 'to_strike_$')
            set_header(ws0, 'I%d' % row, 'to_strike_%')
            row += 1

            for stage in pos.positionstage_set.all():
                for i, name in enumerate(STAGE_NAMES):
                    set_float(ws0, '%s%d' % (ascii_uppercase[i], row), getattr(stage, name))

                set_float(ws0, 'H%d' % row, '=%s-A%d' % (stock_price, row))
                set_percent(ws0, 'I%d' % row, '=1-%s/A%d' % (stock_price, row))
                row += 1

            row += 2

            # condition section
            for i, name in zip([0, 1, 4], CONDITION_NAMES):
                set_header(ws0, '%s%d' % (ascii_uppercase[i], row), name)
            set_header(ws0, 'D%d' % row, 'bool')
            set_header(ws0, 'G%d' % row, 'bool')
            row += 1

            for condition in pos.make_conditions():
                for i, j in zip([0, 1, 4], range(3)):
                    set_float(ws0, '%s%d' % (ascii_uppercase[i], row), condition[j])

                set_float(ws0, 'D%d' % row, make_expr(condition[1], stock_price))
                set_float(ws0, 'G%d' % row, make_expr(condition[2], close_value))

                row += 1

            row += 2

        # set excel stat
        set_header(ws0, 'A%d' % row, 'days')
        set_header(ws0, 'B%d' % row, 'mean vol')
        set_header(ws0, 'C%d' % row, 'remain vol')
        set_header(ws0, 'D%d' % row, 'mean hl')
        set_header(ws0, 'E%d' % row, 'current hl')
        set_header(ws0, 'F%d' % row, 'remain gap')
        for day in [5, 20]:
            row += 1
            set_int(ws0, 'A%d' % row, day)
            set_int(ws0, 'B%d' % row, stat_data[symbol]['mean_vol%d' % day])
            set_value(ws0, 'C%d' % row, '=B%d-%s' % (row, stock_volume))
            set_percent(ws0, 'D%d' % row, stat_data[symbol]['mean_hl%d' % day])
            set_percent(ws0, 'E%d' % row, '=(%s-%s)/%s' % (stock_high, stock_low, stock_open))
            set_percent(ws0, 'F%d' % row, '=D%d-E%d' % (row, row))

        row += 2

        set_header(ws0, 'A%d' % row, 'From %')
        set_header(ws0, 'B%d' % row, 'To %')
        set_header(ws0, 'C%d' % row, 'Bool')
        for i in range(3, 8):
            set_header(ws0, '%s%d' % (ascii_uppercase[i], row), 'Part %d' % (i - 2))

        row += 1

        for stat in stat_data[symbol]['oc_stat']:
            start0, stop0 = stat['close_open']
            expr0 = '=IF(AND(%s<=%s,%s<=%s), TRUE, "")' % (
                start0, close_open, close_open, stop0
            )
            set_percent(ws0, 'A%d' % row, start0)
            set_percent(ws0, 'B%d' % row, stop0)
            set_value(ws0, 'C%d' % row, expr0)

            for i, (start1, stop1) in enumerate(stat['open_close'], start=3):
                temp = '%.2f~%.2f%%' % (start1 * 100, stop1 * 100)
                set_value(ws0, '%s%d' % (ascii_uppercase[i], row), temp)

                expr1 = '=IF(AND(%s<=%s,%s<=%s,C%d=TRUE), TRUE, "")' % (
                    start1, net_chg, net_chg, stop1, row
                )

                set_value(ws0, '%s%d' % (ascii_uppercase[i], row), temp)
                set_value(ws0, '%s%d' % (ascii_uppercase[i], row + 1), expr1)

            row += 2

        row += 2

        # stat predict close stat
        std_value = 'B%d' % (row + 1)
        set_header(ws0, 'B%d' % row, 'stat')
        set_header(ws0, 'C%d' % row, 'bool')
        row += 1
        for i, name in enumerate(CLOSE_STAT):
            set_header(ws0, 'A%d' % (row + i), name)

            proc = set_int
            if name in ('std_value', '60_day_move'):
                proc = set_percent

            proc(
                ws0, 'B%d' % (row + i), stat_data[symbol]['std_close']['std'][name]
            )

        # set bool
        expr = '=IF(%s>=0,%s-%s,%s-%s)' % (
            close_last, std_value, close_last, close_last, std_value
        )  # std diff
        set_percent(ws0, 'C%d' % row, expr)

        expr = '=IF(AND(-%s<=%s,%s<=%s),TRUE,"")' % (
            std_value, close_last, close_last, std_value
        )  # in std
        set_value(ws0, 'C%d' % (row + 1), expr)
        expr = '=IF(OR(-%s>%s,%s>%s),TRUE,"")' % (
            std_value, close_last, close_last, std_value
        )  # out std
        set_value(ws0, 'C%d' % (row + 2), expr)

        expr = '=IF(%s>%s,TRUE,"")' % (close_last, std_value)  # above std
        set_value(ws0, 'C%d' % (row + 3), expr)
        expr = '=IF(%s<-%s,TRUE,"")' % (close_last, std_value)  # below std
        set_value(ws0, 'C%d' % (row + 4), expr)

        expr = '=IF(%s>0,TRUE,"")' % close_last  # close gain
        set_value(ws0, 'C%d' % (row + 5), expr)
        expr = '=IF(%s<0,TRUE,"")' % close_last  # close loss
        set_value(ws0, 'C%d' % (row + 6), expr)

        # consec in std
        row += 9

        set_header(ws0, 'A%d' % row, 'consec')
        set_header(ws0, 'B%d' % row, 'count')
        row += 1
        for index, count in stat_data[symbol]['std_close']['consec']:
            set_value(ws0, 'A%d' % row, '%d days in std' % index)
            set_int(ws0, 'B%d' % row, count)
            row += 1

        row += 2

        # history price
        set_header(ws0, 'A%d' % row, 'date')
        set_header(ws0, 'B%d' % row, 'close')
        set_header(ws0, 'C%d' % row, 'volume')
        set_header(ws0, 'D%d' % row, 'close_chg')
        set_header(ws0, 'E%d' % row, 'pct_chg')
        set_header(ws0, 'F%d' % row, 'consec')
        set_header(ws0, 'G%d' % row, 'out_std')
        set_header(ws0, 'H%d' % row, 'above_std')
        set_header(ws0, 'I%d' % row, 'below_std')
        row += 1

        for history in stat_data[symbol]['std_close']['history']:
            set_value(ws0, 'A%d' % row, history['date'].strftime('%Y-%m-%d'))
            set_float(ws0, 'B%d' % row, history['close'])
            set_int(ws0, 'C%d' % row, history['volume'])
            set_float(ws0, 'D%d' % row, history['close_chg'])
            set_percent(ws0, 'E%d' % row, history['pct_chg'])
            set_int(ws0, 'F%d' % row, history['consec'])
            set_value(ws0, 'G%d' % row, '=IF(%s,TRUE,"")' % history['out_std'])
            set_value(ws0, 'H%d' % row, '=IF(%s,TRUE,"")' % history['above_std'])
            set_value(ws0, 'I%d' % row, '=IF(%s,TRUE,"")' % history['below_std'])

            row += 1

    wb._active_sheet_index = 0
    wb.save(EXCEL_FILE)

    # open excel file
    os.startfile(EXCEL_FILE)

    return redirect(reverse('admin:app_list', args=('statement', )))


# todo: need move symbol with diff strategy test
