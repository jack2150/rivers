import json
from django.core.urlresolvers import reverse
from django.shortcuts import render
from data.get_data import GetData
from opinion.group.stat.stats import ReportStatPrice


def report_statstem(request, symbol, percent, bdays):
    """

    :param request:
    :param symbol:
    :param percent:
    :param bdays:
    :return:
    """
    df_stock = GetData.get_stock_data(symbol)
    report_stat = ReportStatPrice(df_stock)
    df_stem = report_stat.stem(percent=int(percent), days=int(bdays))

    stem_columns = {
        'move': [str(i) for i in df_stem.index],
        'count': [int(i) for i in df_stem['chance']],
        'sum': [abs(int(i)) for i in df_stem['sum']],
        # 'abs_move': [str(i) for i in df_stem.index ]
    }
    # print stem_columns

    stem_data = []
    for index, data in df_stem.iterrows():
        data['range'] = str(index)
        stem_data.append(dict(data))
    stem_data = json.dumps(stem_data)

    title = 'Report price stem | %s' % symbol.upper()
    template = 'opinion/stat/stem.html'
    parameters = dict(
        site_title=title,
        title=title,
        symbol=symbol,
        percent=percent,
        bdays=bdays,
        stem_columns=stem_columns,
        stem_data=stem_data,
    )

    return render(request, template, parameters)


# noinspection SpellCheckingInspection
def report_statprice(request, symbol):
    """

    :param request:
    :param symbol:
    :return:
    """
    df_stock = GetData.get_stock_data(symbol)
    report_stat = ReportStatPrice(df_stock)
    main_stat = report_stat.main_stat()

    df_group = report_stat.move_dist()
    # print len(df_up), len(df_down)
    # ts(df_up)
    # ts(df_down)

    move_dist_columns = {
        'move': [str(i) for i in df_group.index],
        'count': [int(i) for i in df_group['chance']],
        'cumsum': [int(i) for i in df_group['cumsum0']],
    }

    move_dist_data = []
    for index, data in df_group.iterrows():
        data['range'] = str(index)
        move_dist_data.append(dict(data))
    move_dist_data = json.dumps(move_dist_data)

    # print json.dumps(move_dist_data)
    bdays_data = {}
    bdays_charts = {}
    for days in (5, 20, 60):
        df_move = report_stat.bday_dist(days)
        # bdays_data['bdays%d' % days] = df_move
        bdays_temp = []
        for index, data in df_move.iterrows():
            data['range'] = str(index)
            percent = int(str(index).split(',')[1][:-1].strip())
            # print percent
            data['stem'] = reverse(
                'report_statstem', kwargs={
                    'symbol': symbol.lower(), 'percent': percent, 'bdays': days
                }
            )

            bdays_temp.append(dict(data))

        bdays_data['bdays%d' % days] = json.dumps(bdays_temp)

        bdays_charts['bdays%d' % days] = {
            'move': [str(i) for i in df_move.index],
            'bull': [int(i) for i in df_move['d_bull']],
            'bear': [int(i) for i in df_move['d_bear']],
        }

    title = 'Report statistics | %s' % symbol.upper()
    template = 'opinion/stat/index.html'
    parameters = dict(
        site_title=title,
        title=title,
        symbol=symbol,
        date0=report_stat.date0,
        date1=report_stat.date1,
        main_stat=main_stat,
        move_dist_columns=move_dist_columns,
        move_dist_data=move_dist_data,
        bdays_data=bdays_data,
        bdays_charts=bdays_charts,
    )

    return render(request, template, parameters)
