import logging
import os
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

logger = logging.getLogger('views')


def clean_normal_h5(request, symbol):
    """
    Clean valid df_normal column
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Start cli for clean_normal: %s' % symbol.upper())
    os.system("start cmd /k python data/manage.py read_clean --symbol=%s --name=normal" % symbol)

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))


def clean_split_new_h5(request, symbol):
    """
    Clean valid df_split/new column
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Start cli for clean_split_new: %s' % symbol.upper())
    os.system("start cmd /k python data/manage.py read_clean --symbol=%s --name=split/new" % symbol)

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))


def clean_split_old_h5(request, symbol):
    """
    Clean valid df_split/old column
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Start cli for clean_split_old: %s' % symbol.upper())
    os.system("start cmd /k python data/manage.py read_clean --symbol=%s --name=split/old" % symbol)

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))
