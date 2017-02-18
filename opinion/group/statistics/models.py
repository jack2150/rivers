from django.db import models
from opinion.group.report.models import ReportEnter


class StatisticsData(models.Model):
    report = models.OneToOneField(ReportEnter, null=True, blank=True)


class StatisticsVolatility(models.Model):
    stat_data = models.OneToOneField(StatisticsData)

    # today option statistics
    iv_52w_high = models.FloatField(default=0, help_text='IV 52 weeks high')
    iv_52w_low = models.FloatField(default=0, help_text='IV 52 weeks high')
    iv_percentile = models.IntegerField(default=50, help_text='Short period')

    hv_52w_high = models.FloatField(default=0, help_text='HV 52 weeks high')
    hv_52w_low = models.FloatField(default=0, help_text='HV 52 weeks high')
    hv_percentile = models.IntegerField(default=50, help_text='Short period')

    iv = models.FloatField(default=0, help_text='Current IV')

    # probability analysis chart
    cycle_date = models.DateField(null=True, blank=True, help_text='Nearest 30 dte date')
    price_upper = models.DecimalField(
        max_digits=10, decimal_places=2, help_text='Price upper cross 1 sd'
    )
    price_lower = models.DecimalField(
        max_digits=10, decimal_places=2, help_text='Price lower cross 1 sd'
    )
    iv_desc = models.TextField(
        blank=True, default='', help_text='Take 5 mins, analysis & projection'
    )


# todo: to be cont