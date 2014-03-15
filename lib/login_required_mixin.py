from django.contrib.auth.decorators import login_required


class LoginRequiredMixin(object):
    def as_view(cls):
        return login_required(super(LoginRequiredMixin, cls).as_view())
