from django.db import models


class BehaviorOpinion(models.Model):
    """
    Emotion and trading condition analysis, daily update
    """
    date = models.DateField(unique=True)

    prospect_theory = models.BooleanField(
        default=True, help_text='Hold on to losers too long and sell winners too soon.'
    )
    belief_perseverance = models.BooleanField(
        default=True, help_text='Opinion keep too long not update; skeptical/misinterpret new info'
    )
    anchoring = models.BooleanField(
        default=True, help_text='Wrong estimate initial stock value with adjustment'
    )
    over_confidence = models.BooleanField(
        default=True, help_text='Overestimate growth forecast, overemphasize '
                                'good news and ignore negative news'
    )
    confirmation_bias = models.BooleanField(
        default=True,
        help_text='Do you believe your positions is good, find news supports that opinions but mis-value'
    )
    self_attribution = models.BooleanField(
        default=True, help_text='Do you blame failure on bad luck, or overestimate your research'
    )
    noise_trading = models.BooleanField(
        default=True, help_text='Using nonprofessionals with no special information to trade'
    )
    hindsight_bias = models.BooleanField(
        default=True, help_text='Do you think that you can predict better than analysts?'
    )
    escalation_bias = models.BooleanField(
        default=True, help_text='Do you put more money because of failure?'
    )
    miss_opportunity = models.BooleanField(
        default=True, help_text='You trade because you afraid of miss opportunity?'
    )
    serious_analysis = models.BooleanField(
        default=False, help_text='Do you seriously look for the bad news on the valuation?'
    )
    trade_addict = models.BooleanField(
        default=True, help_text='Are you addict for trading? Trade cause you want trade'
    )
    other_mistake = models.TextField(
        default='', blank=True, help_text='Write down other mistake you done'
    )
    other_accurate = models.TextField(
        default='', blank=True, help_text='Write down other correct/valid things you done'
    )


