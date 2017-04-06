from django.contrib import admin
from opinion.views import *
from opinion.group.stock.admin import *
from opinion.group.market.admin import *
from opinion.group.mindset.admin import *
from opinion.group.quest.admin import *
from opinion.group.position.admin import *
from opinion.group.technical.admin import *
from opinion.group.report.admin import *


admin.site.register_view(
    'opinion/profile/link/(?P<symbol>\w+)/$',
    urlname='opinion_link', view=opinion_link
)
