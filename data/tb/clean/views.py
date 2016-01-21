import logging
import os
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

logger = logging.getLogger('views')


def clean_valid_h5(request, symbol, name):
    """
    Clean valid df_normal column

    :param request: request
    :param symbol: str
    :param name: str ('normal', 'split_old', 'split_new')
    :return: render
    """
    name = name.replace('_', '/')

    logger.info('Start cli for clean: %s %s' % (symbol.upper(), name))
    os.system("start cmd /k python data/manage.py read_clean --symbol=%s --name=%s" % (
        symbol, name
    ))

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))
