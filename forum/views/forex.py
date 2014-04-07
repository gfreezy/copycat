import datetime
import pytz
from django.views.generic import TemplateView
from django.conf import settings
from django.utils import timezone
from forum.models import Forex, ImportEvent


class ForexView(TemplateView):
    template_name = 'forex/list.html'

    def get_context_data(self, **kwargs):
        ctx = super(ForexView, self).get_context_data(**kwargs)

        d = self.request.GET.get('date')
        today = timezone.now()
        try:
            date_str = datetime.datetime.strptime(d, '%Y-%m-%d')
            date = timezone.make_aware(date_str, pytz.timezone(settings.TIME_ZONE))
        except:
            date = today
        forex = Forex.objects.filter(time__year=date.year, time__month=date.month, time__day=date.day).order_by('-time')
        events = ImportEvent.objects.filter(time__year=date.year, time__month=date.month, time__day=date.day).order_by('-time')

        ctx['today'] = today
        ctx['date'] = date
        ctx['tab'] = 'forex'
        ctx['forex'] = forex
        ctx['events'] = events
        return ctx