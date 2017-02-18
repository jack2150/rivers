from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import render
from pandas.tseries.offsets import BDay

from opinion.group.fundamental.models import StockFundamental, StockIndustry, UnderlyingArticle
from opinion.group.fundamental.report import ReportFundamental
from opinion.group.position.models import PositionIdea, PositionEnter, PositionDecision
from opinion.group.report.models import ReportEnter
from opinion.group.technical.report import ReportTechnicalRank
from opinion.group.technical.models import TechnicalRank, TechnicalOpinion


MODEL_OBJ = {
    'positionidea': PositionIdea,
    'technicalrank': TechnicalRank,
    'technicalopinion': TechnicalOpinion,
    'stockfundamental': StockFundamental,
    'stockindustry': StockIndustry,
    'underlyingarticle': UnderlyingArticle,
    'positionenter': PositionEnter,
    'positiondecision': PositionDecision,

}


def opinion_link(request, symbol):
    """

    :param request:
    :param symbol:
    :return:
    """
    symbol = symbol.upper()

    template = 'opinion/opinion_link.html'

    parameters = dict(
        site_title='Opinion links',
        title='{symbol} opinions links'.format(symbol=symbol),
        symbol=symbol
    )

    return render(request, template, parameters)


def generate_report(request, symbol, date=''):
    """
    Step by step create opinion then final create report
    :param request: request
    :param symbol: str
    :param date: str
    :return: render
    """
    symbol = symbol.upper()

    if date == '':
        date = datetime.today().date()
        if date.weekday() not in range(1, 6):  # only weekday
            # noinspection PyUnresolvedReferences
            date = (date - BDay()).to_datetime().date()
    else:
        date = datetime.strptime(date, '%Y-%m-%d')

    # 1. create stock report, if exist open it
    report_enter, exists = ReportEnter.objects.get_or_create(
        symbol=symbol, date=date
    )
    # print date, report_enter, exists

    report_enter = report_enter
    """:type: StockReport"""

    model_data = {}

    for key, model in MODEL_OBJ.items():
        model_data[key] = {}
        try:
            model_data[key]['data'] = getattr(report_enter, key)
        except ObjectDoesNotExist:
            model_data[key]['data'] = model()
            model_data[key]['data'].report = report_enter
            model_data[key]['data'].save()

        model_data[key]['url'] = reverse(
            'admin:opinion_%s_change' % key, args=(model_data[key]['data'].id,)
        )

    model_data['stockreport'] = {
        'data': report_enter,
        'url': reverse(
            'admin:opinion_reportenter_change', args=(report_enter.id,)
        )
    }

    # page
    template = 'opinion/report/index.html'
    parameters = dict(
        site_title='Create report | %s | %s' % (symbol, date),
        title='Create report | %s | %s' % (symbol, date),
        report_enter=report_enter,
        symbol=symbol,
        model_data=model_data
    )

    return render(request, template, parameters)


def reference_link(request, report_id, model):
    """

    :param request:
    :param report_id:
    :param model:
    :return:
    """
    report_enter = ReportEnter.objects.get(id=report_id)
    symbol = report_enter.symbol.upper()

    # summary
    model_data = {
        k: getattr(report_enter, k) for k, v in MODEL_OBJ.items()
    }

    # todo: only check opinion item exists
    op_exists = OpinionExists(report_enter)
    summary = op_exists.created()

    template = 'opinion/report/helper.html'
    parameters = dict(
        site_title='Reference | %s | %s' % (symbol, model),
        title='Reference | %s | %s' % (symbol, model),
        symbol=symbol,
        model=model,
        model_data=model_data,
        summary=summary,
    )

    return render(request, template, parameters)


class OpinionExists(object):
    def __init__(self, report_enter):
        self.report_enter = report_enter
        """:type: ReportEnter """

    @staticmethod
    def exists(parent, rel_obj):
        try:
            if getattr(parent, rel_obj):
                return True
        except ObjectDoesNotExist:
            return False

    def created(self):
        stock_fd = False
        if self.exists(self.report_enter, 'stockfundamental'):
            if self.report_enter.stockfundamental.tp_mean > 0:
                stock_fd = True

        stock_id = False
        if self.exists(self.report_enter, 'stockindustry'):
            if self.report_enter.stockindustry.direction:
                stock_id = True

        pos_idea = False
        if self.exists(self.report_enter, 'positionidea'):
            if self.report_enter.positionidea.target_price > 0:
                pos_idea = True

        pos_enter = False
        if self.exists(self.report_enter, 'positionenter'):
            if self.report_enter.positionenter.target_price > 0:
                pos_enter = True

        pos_dc = False
        if self.exists(self.report_enter, 'positiondecision'):
            if len(self.report_enter.positiondecision.desc):
                pos_dc = True

        tech_me = False
        if self.exists(self.report_enter.technicalrank, 'technicalmarketedge'):
            if self.report_enter.technicalrank.technicalmarketedge.fprice:
                tech_me = True

        tech_bc = False
        if self.exists(self.report_enter.technicalrank, 'technicalbarchart'):
            if self.report_enter.technicalrank.technicalbarchart.strength:
                tech_bc = True

        tech_cm = False
        if self.exists(self.report_enter.technicalrank, 'technicalchartmill'):
            if self.report_enter.technicalrank.technicalchartmill.rank:
                tech_cm = True

        article = False
        if self.exists(self.report_enter, 'underlyingarticle'):
            if len(self.report_enter.underlyingarticle.article_name):
                article = True

        # todo: here
        opinions = [
            'TechnicalTick', 'TechnicalSma', 'TechnicalVolume', 'TechnicalIchimoku',
            'TechnicalParabolic', 'TechnicalStoch', 'TechnicalBand', 'TechnicalFw',
            'TechnicalTTM', 'TechnicalPivot', 'TechnicalFreeMove', 'TechnicalZigZag',
        ]
        tech_op = []
        if self.report_enter.technicalopinion.id:
            for op in opinions:
                created = 'Waiting...'
                if self.exists(self.report_enter.technicalopinion, op.lower()):
                    created = 'Yes'

                tech_op.append('%s %s' % (op.replace('Technical', ''), created))

        return {
            'stockfundamental': 'Yes' if stock_fd else 'Waiting...',
            'stockindustry': 'Yes' if stock_id else 'Waiting...',
            'positionidea': 'Yes' if pos_idea else 'Waiting...',
            'positionenter': 'Yes' if pos_enter else 'Waiting...',
            'positiondecision': 'Yes' if pos_dc else 'Waiting...',
            'underlyingarticle': 'Yes' if article else 'Waiting...',
            'technicalrank': [
                '%s %s' % ('Marketedge', 'Yes' if tech_me else 'Waiting...'),
                '%s %s' % ('barchart', 'Yes' if tech_bc else 'Waiting...'),
                '%s %s' % ('chartmill', 'Yes' if tech_cm else 'Waiting...'),
            ],
            'technicalopinion': tech_op
        }


def enter_report(request, report_id):
    """

    :param request:
    :param symbol:
    :param date:
    :return:
    """
    report_enter = ReportEnter.objects.get(id=report_id)
    tech_rank_report = ReportTechnicalRank(report_enter.technicalrank, report_enter.close)
    fd_report = ReportFundamental(report_enter)

    reports = {
        # technical rank
        'marketedge': tech_rank_report.marketedge.create(),
        'barchart': tech_rank_report.barchart.create(),
        'chartmill': tech_rank_report.chartmill.create(),
        # stock fundamental
        'fundamental': fd_report.stock_fd.create(),
        'industry': fd_report.stock_id.create(),

    }
    # report_enter.technicalrank.technicalmarketedge.recommend

    # todo: here, tomorrow, if clv not profit, close it
    # todo: start closing most of the pos and wait next time

    heats = {
        'marketedge': tech_rank_report.marketedge.to_heat(),
        'barchart': tech_rank_report.barchart.to_heat(),
        'chartmill': tech_rank_report.chartmill.to_heat(),
    }




    title = 'Enter report | %s | %s' % (report_enter.symbol, report_enter.date)
    template = 'opinion/report/summary.html'
    parameters = dict(
        site_title=title,
        title=title,
        report_enter=report_enter,
        reports=reports,
        symbol=report_enter.symbol,
        date=report_enter.date
    )

    return render(request, template, parameters)






# todo: symbol date report, for all detail, position & technical
# todo: market & mindset & quest date report, all market
