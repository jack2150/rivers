import logging
import os
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

logger = logging.getLogger('views')


def fillna_missing_h5(request, symbol, name):
    """
    Fill missing rows for df_normal
    :param request: request
    :param symbol: str
    :param name: str ('normal', 'split/old', 'split/new')
    :return: render
    """
    name = name.replace('_', '/')

    logger.info('Start cli for fillna_%s: %s' % (name, symbol))
    os.system("start cmd /k python data/manage.py fillna_missing --symbol=%s --name=%s" % (
        symbol, name
    ))

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))
