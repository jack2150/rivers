from django.db import models


class PortfolioPolicy(models.Model):
    """
    Major holder for
    """
    name = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)


class PortfolioAllocation(models.Model):
    """
    A script that use for select multi-set of symbol with different category
    for example: value set & grow set, sectors set, high/low risk set
    A set contain a list of symbol that ready for use
    """
    name = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)


class PortfolioApproach(models.Model):
    """

    """
    name = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)


class PortfolioPerformance(models.Model):
    """
    Use for tracking portfolio result
    """
    name = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)

# todo: start writing from chapter 7
# todo: policy, risk and others can add later
# todo: back to research
