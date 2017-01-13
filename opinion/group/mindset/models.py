import datetime
from django.db import models


class MindsetNote(models.Model):
    """
    Note that you read everyday for before trading
    """
    date = models.DateField(default=datetime.datetime.now)
    category = models.CharField(
        max_length=20, default='behavior',
        choices=(
            ('trade', 'Trade'), ('behavior', 'Behavior'),
            ('other', 'Other')
        )
    )

    note = models.CharField(max_length=200)
    explain = models.TextField()


class MindsetBehavior(models.Model):
    """
    Emotion and trading condition analysis, daily update
    """
    date = models.DateField(unique=True, default=datetime.datetime.now)

    # enter
    emotion_think = models.BooleanField(
        default=True, help_text='I trade using emotion not logic thinking'
    )
    trade_control = models.BooleanField(
        default=True, help_text='I not control myself when entering a bad trade'
    )
    bad_prepare = models.BooleanField(
        default=True, help_text='I not prepare all possible and have wrong guess'
    )

    # mindset
    over_confident = models.BooleanField(
        default=True, help_text='I have > 70% confidence and not skeptical at all'
    )
    size_matter = models.BooleanField(
        default=True, help_text='I trade too big, position not fit into portfolio rule'
    )
    noise_news = models.BooleanField(
        default=True, help_text='I listen to noise news and not the fact'
    )
    listen_because = models.BooleanField(
        default=True, help_text='I listen to because on news'
    )
    confirm_bias = models.BooleanField(
        default=True, help_text='I only look to things that support my view'
    )
    prove_wrong = models.BooleanField(
        default=True, help_text='I do not prove my analysis wrong again and again'
    )
    conservatism_bias = models.BooleanField(
        default=True, help_text='I keep my view too long without news update'
    )
    attention_blind = models.BooleanField(
        default=True, help_text='I not keep up all the market news and blind to them'
    )
    hold_power = models.BooleanField(
        default=True, help_text='I not hold because fact not changing'
    )
    crown_pick = models.BooleanField(
        default=True, help_text='I will follow majority because I stupid'
    )
    not_contrarian = models.BooleanField(
        default=True, help_text='I not a contrarian trader that do crazy thing'
    )
    stick_yourself = models.BooleanField(
        default=True, help_text='I do not stick to my trading plan'
    )
    loss_aversion = models.BooleanField(
        default=True, help_text='I strongly want to avoid loss that obtain gain'
    )
    quo_bias = models.BooleanField(
        default=True, help_text='I do not wish to own what I previously own'
    )
    no_process = models.BooleanField(
        default=True, help_text='I do not focus on process and just trade'
    )
    shortcut = models.BooleanField(
        default=True, help_text='I just want shortcut from trading'
    )
    outcome_bias = models.BooleanField(
        default=True, help_text='I make profit so I always right'
    )

    self_attribute = models.BooleanField(
        default=True, help_text='Do you blame failure on bad luck, or overestimate your research'
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
    trade_addict = models.BooleanField(
        default=True, help_text='Are you addict for trading? Trade cause you want trade'
    )

    decision_time = models.BooleanField(
        default=True, help_text='You have wrong mindset, no enter or close the trade now'
    )

    other_mistake = models.TextField(
        default='', blank=True, help_text='Write down other mistake you done'
    )
    other_accurate = models.TextField(
        default='', blank=True, help_text='Write down other correct/valid things you done'
    )


class MindsetLossHold(models.Model):
    """
    Most important behavior checklist
    """
    symbol = models.CharField(max_length=20)
    date = models.DateField()
    unique_together = (('symbol', 'date'), )

    # admit
    wrong_admit = models.BooleanField(
        default=True, help_text='I was wrong because rational not work'
    )
    bad_analysis = models.BooleanField(
        default=True, help_text='Not valid analysis & reason on trade'
    )
    good_luck = models.BooleanField(
        default=True, help_text='It was not good luck enough to profit'
    )
    lazy_update = models.BooleanField(
        default=True, help_text='I was lazy not keep update on price & news'
    )

    # primary
    loss_more = models.BooleanField(
        default=True, help_text='Position loss more than expected'
    )
    irrational = models.BooleanField(
        default=True, help_text='No valid reason but keep trend loss'
    )
    new_highlow = models.BooleanField(
        default=True, help_text='Out of current range, to new high/low'
    )
    valid_reverse = models.BooleanField(
        default=True,
        help_text='If all 3 above true, reverse position and make money back it keep trending'
    )

    # take it
    avoid_now = models.BooleanField(
        default=True, help_text='It is painful but I will close it and avoid this'
    )
    take_loss = models.BooleanField(
        default=True, help_text='It is painful but I will close it and keep cash for later'
    )


class MindsetLossExcuse(models.Model):
    """
    Excuse checklist when loss happen
    """
    symbol = models.CharField(max_length=20)
    date = models.DateField(default=datetime.datetime.now)  #
    unique_together = (('symbol', 'date'),)

    only_if = models.BooleanField(
        default=True, help_text='You think if this happen, I will be profit'
    )
    outside_occur = models.BooleanField(
        default=True, help_text='Something outside analysis occur, it not my fault'
    )
    almost_right = models.BooleanField(
        default=True, help_text='I almost right, just a bit more'
    )
    still_come = models.BooleanField(
        default=True, help_text='Just not happen yet, I will wait'
    )
    single_predict = models.BooleanField(
        default=True, help_text='You cannot judge me by this wrong only'
    )
    out_trouble = models.BooleanField(
        default=True, help_text='I cant get out while I can because is painful'
    )
    response_now = models.BooleanField(
        default=True, help_text='I will be quickly to adjust this trade now'
    )



# todo: a view that show all recent opinion on a given symbol

# todo: easy to daily comment symbol by symbol, TabularInline or StackedInline
# todo: roll back interface...








