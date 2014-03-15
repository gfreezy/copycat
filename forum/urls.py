from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse_lazy
from forum.views.auth import Register
from forum.views.topics import New


urlpatterns = patterns('',
    url(r'^$', 'forum.views.root.index', name='index'),

    # auth
    url(r'^login$', 'django.contrib.auth.views.login', {'template_name': 'auth/login.html'}, name='login'),
    url(r'^logout$', 'django.contrib.auth.views.logout_then_login', name='logout'),
    url(r'^password_reset$',
        'django.contrib.auth.views.password_reset',
        {
            'template_name': 'auth/password_reset.html',
            'email_template_name': 'auth/password_reset_email.html',
            'subject_template_name': 'auth/password_reset_subject.txt',
        },
        name='password_reset'),
    url(r'^password_reset_done$', 'django.contrib.auth.views.password_reset_done', {'template_name': 'auth/password_reset_done.html'}, name='password_reset_done'),
    url(r'^password_reset_confirm/(?P<uidb64>.+?)/(?P<token>.+?)$',
        'django.contrib.auth.views.password_reset_confirm',
        {
            'template_name': 'auth/password_reset_confirm.html',
            'post_reset_redirect': reverse_lazy('login')
        },
        name='password_reset_confirm'),

    url(r'^register$', Register.as_view(), name='register'),

    # topic
    url(r'^t/(?P<id>\d+)$', 'forum.views.topics.show', name='topic'),
    url(r'^t/(?P<id>\d+)/reply$', 'forum.views.topics.reply', name='reply'),
    url(r'^new/(?P<slug>\w+)$', New.as_view(), name='new_topic'),

    # user
    url(r'^member/(?P<name>\w+)', 'forum.views.root.index', name='user'),
    url(r'^member/(?P<name>\w+)/topics$', 'forum.views.root.index', name='user_topics'),
    url(r'^member/(?P<name>\w+)/replies$', 'forum.views.root.index', name='user_replies'),
    url(r'^member/(?P<name>\w+)/favourites$', 'forum.views.root.index', name='user_favourites'),

    # node
    url(r'^go/(?P<slug>\w+)$', 'forum.views.nodes.show', name='node'),
)
