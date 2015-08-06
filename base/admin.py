from django.contrib import admin
from base.views import df_html_view


admin.site.register_view(
    'simulation/strategyresult/df_to_html/(?P<result>\w+)/(?P<result_id>\d+)/$',
    urlname='df_html_view', view=df_html_view
)