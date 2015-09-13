from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from checklist.models import *
from data.models import Stock
from simulation.models import StrategyResult
from statement.models import *


def position_spreads(request, date):
    """
    Position spread view
    :param request: request
    :param date: str
    :return: render
    """
    if date:
        statement = Statement.objects.get(date=date)
        """:type: Statement"""
    else:
        statement = Statement.objects.order_by('date').last()
        """:type: Statement"""

    positions = Position.objects.filter(
        id__in=[p[0] for p in statement.profitloss_set.values_list('position')]
    ).order_by('symbol')

    spreads = list()
    for position in positions:
        if position.name == 'STOCK':
            stage = position.current_stage(
                position.holdingequity_set.get(statement__date=date).close_price
            )
        else:
            try:
                stage = position.current_stage(float(Stock.get_price(position.symbol, date).close))
            except ObjectDoesNotExist:
                stage = None

        opinion = dict(exists=False, condition='UNKNOWN', action='HOLD', name='')
        holding_opinion = position.holdingopinion_set.filter(date=date)
        if holding_opinion.exists():
            holding_opinion = holding_opinion.first()
            opinion['name'] = 'hold'
            opinion['exists'] = True
            opinion['condition'] = holding_opinion.condition
            opinion['action'] = holding_opinion.action

        exit_opinion = position.exitopinion_set.filter(date=date)
        if exit_opinion.exists():
            opinion['name'] = 'exit'
            opinion['exists'] = True
            opinion['action'] = 'CLOSE'

        spreads.append(dict(
            position=position,
            profit_loss=position.profitloss_set.get(statement__date=date),
            opinion=opinion,
            stage=stage,
        ))

    template = 'statement/position/spreads.html'
    parameters = dict(
        site_title='Position Spreads',
        title='Spreads',
        spreads=spreads,
        date=date
    )

    return render(request, template, parameters)


# noinspection PyShadowingBuiltins
def create_opinion(request, opinion, id, date):
    """
    Get existing or create new holding opinion
    :param request: request
    :param id: int
    :param date: str
    :return: render
    """
    position = Position.objects.get(id=id)

    if opinion == 'hold':
        try:
            # exists open it
            holding_opinion = HoldingOpinion.objects.get(Q(position=position) & Q(date=date))
            link = reverse('admin:checklist_holdingopinion_change', args=(holding_opinion.id,))
        except ObjectDoesNotExist:
            # not exists create new
            holding_opinion = HoldingOpinion()
            holding_opinion.position = position
            holding_opinion.date = date
            holding_opinion.save()
            link = reverse('admin:checklist_holdingopinion_change', args=(holding_opinion.id,))
    elif opinion == 'exit':
        try:
            exit_opinion = ExitOpinion.objects.get(Q(position=position) & Q(date=date))
            link = reverse('admin:checklist_exitopinion_change', args=(exit_opinion.id,))
        except ObjectDoesNotExist:
            exit_opinion = ExitOpinion()
            exit_opinion.position = position
            exit_opinion.date = date
            exit_opinion.save()
            link = reverse('admin:checklist_exitopinion_change', args=(exit_opinion.id,))
    else:
        raise ValueError('Invalid url argument opinion.')

    return redirect(link)


class BlindPositionForm(forms.Form):
    position = forms.IntegerField(widget=forms.HiddenInput)
    strategy_result = forms.IntegerField()

    def clean(self):
        pos_id = self.cleaned_data['position']
        sr_id = self.cleaned_data['strategy_result']

        position = None
        try:
            position = Position.objects.get(id=int(pos_id))
        except ObjectDoesNotExist:
            self._errors['position'] = self.error_class(
                ['Position id: {id} not found.'.format(id=pos_id)]
            )

        strategy_result = None
        try:
            strategy_result = StrategyResult.objects.get(id=int(sr_id))
        except ObjectDoesNotExist:
            self._errors['strategy_result'] = self.error_class(
                ['Strategy result id: {id} not found.'.format(id=sr_id)]
            )

        # make sure both are same symbol
        if position and strategy_result:
            if position.symbol != strategy_result.symbol:
                self._errors['position'] = self.error_class(
                    ['Different symbol {symbol0} and {symbol1}'.format(
                        symbol0=position.symbol,
                        symbol1=strategy_result.symbol
                    )]
                )

        return self.cleaned_data


# noinspection PyShadowingBuiltins
def blind_strategy(request, id):
    """
    A position can be blind into a strategy result for anlaysis
    :param request:
    :param id: int
    :return:
    """
    position = Position.objects.get(id=id)

    strategy_results = StrategyResult.objects.filter(symbol=position.symbol)
    if strategy_results.exists():
        strategy_results = strategy_results.order_by('id').reverse()

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = BlindPositionForm(request.POST)

        if form.is_valid():
            position_id = form.cleaned_data['position']
            strategy_result_id = form.cleaned_data['strategy_result']
            strategy_result = StrategyResult.objects.get(id=strategy_result_id)

            position = Position.objects.get(id=position_id)
            position.strategy_result = strategy_result
            position.save()

            return redirect(reverse('admin:statement_position_change', args=(position.id,)))
    else:
        form = BlindPositionForm(initial={
            'position': id
        })

    template = 'statement/position/blind.html'
    parameters = dict(
        site_title='Position blind strategy',
        title='Blinding strategy',
        position=position,
        form=form,
        strategy_results=strategy_results
    )

    return render(request, template, parameters)

# todo: quant into another db
