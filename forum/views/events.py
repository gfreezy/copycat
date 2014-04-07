import datetime
import pytz
from django.views.generic.list import ListView
from django.conf import settings
from django.utils import timezone
from forum.models import EconomicEvent


class EventsView(ListView):
    template_name = 'events/list.html'
    model = EconomicEvent
    paginate_by = 50

    def get_queryset(self):
        today = datetime.datetime.today()
        d = self.request.GET.get('date')
        try:
            date = datetime.datetime.strptime(d, '%Y-%m-%d')
        except Exception:
            date = today
        date = timezone.make_aware(date, pytz.timezone(settings.TIME_ZONE))
        self.date = date
        return EconomicEvent.objects.filter(time__year=date.year, time__month=date.month, time__day=date.day).order_by('-time')

    def get_context_data(self, **kwargs):
        ctx = super(EventsView, self).get_context_data(**kwargs)
        now = datetime.datetime.now()
        today = timezone.make_aware(now, pytz.timezone(settings.TIME_ZONE))
        ctx['today'] = today
        ctx['date'] = self.date
        ctx['tab'] = 'events'
        return ctx
