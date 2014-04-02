import datetime
import pytz
from django.views.generic.list import ListView
from django.conf import settings
from forum.models import Forex


class ForexView(ListView):
    template_name = 'forex/list.html'
    model = Forex
    paginate_by = 50

    def get_queryset(self):
        return Forex.objects.order_by('-time')

    def get_context_data(self, **kwargs):
        ctx = super(ForexView, self).get_context_data(**kwargs)
        now = datetime.datetime.now()
        today = datetime.datetime(now.year, now.month, now.day, tzinfo=pytz.timezone(settings.TIME_ZONE))
        ctx['today'] = today
        ctx['tab'] = 'forex'
        return ctx