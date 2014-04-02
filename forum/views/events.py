import datetime
import pytz
from django.views.generic.list import ListView
from django.conf import settings
from forum.models import EconomicEvent


class EventsView(ListView):
    template_name = 'events/list.html'
    model = EconomicEvent
    paginate_by = 50

    def get_queryset(self):
        return EconomicEvent.objects.order_by('-time')

    def get_context_data(self, **kwargs):
        ctx = super(EventsView, self).get_context_data(**kwargs)
        now = datetime.datetime.now()
        today = datetime.datetime(now.year, now.month, now.day, tzinfo=pytz.timezone(settings.TIME_ZONE))
        ctx['today'] = today
        ctx['tab'] = 'events'
        return ctx