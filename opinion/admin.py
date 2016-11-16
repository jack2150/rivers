from django.contrib import admin
from opinion.views import *


admin.site.register_view(
    'opinion/profile/link/(?P<symbol>\w+)/$',
    urlname='opinion_link', view=opinion_link
)


