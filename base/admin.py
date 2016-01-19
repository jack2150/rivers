from base.views import *
from rivers.urls import *

admin.site.register_view(
    'data/df/(?P<model>\w+)/(?P<id>\d+)/$',
    urlname='df_view', view=df_view
)
