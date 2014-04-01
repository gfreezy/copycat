import datetime
from django.views.generic.list import ListView
from django.utils import timezone
from forum.models import EconomicEvent


class EventsView(ListView):
    template_name = 'events/list.html'
    model = EconomicEvent
    paginate_by = 50

    def get_queryset(self):
        return EconomicEvent.objects.order_by('-time')

    def get_context_data(self, **kwargs):
        ctx = super(EventsView, self).get_context_data(**kwargs)
        now = timezone.now()
        today = datetime.datetime(now.year, now.month, now.day, tzinfo=now.tzinfo)
        ctx['today'] = today
        ctx['tab'] = 'events'
        return ctx