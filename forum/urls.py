import forum.views.topics
import forum.views.users
import forum.views.nodes
import forum.views.blogs
import forum.views.root
import forum.views.pages
import forum.views.events
import forum.views.forex
import forum.views.auth
from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse_lazy
from forum.views.auth import RegisterView, AuthenticationForm


urlpatterns = patterns(
    '',
    url(r'^$', forum.views.root.index, name='index'),
    # auth
    url(r'^login$',
        'django.contrib.auth.views.login',
        {
            'template_name': 'auth/login.html',
            'authentication_form': AuthenticationForm,
            'extra_context': {
                'social_sites': forum.views.social_sites,
            },
        },
        name='login'
    ),
    url(r'^login/(?P<provider>.*?)$', forum.views.auth.oauth, name='oauth'),
    url(r'^logout$', 'django.contrib.auth.views.logout_then_login', name='logout'),
    url(r'^password_reset$',
        'django.contrib.auth.views.password_reset',
        {
            'template_name': 'auth/password_reset.html',
            'email_template_name': 'auth/password_reset_email.html',
            'subject_template_name': 'auth/password_reset_subject.txt',
        },
        name='password_reset'
    ),
    url(r'^password_reset_done$', 'django.contrib.auth.views.password_reset_done', {'template_name': 'auth/password_reset_done.html'}, name='password_reset_done'),
    url(r'^password_reset_confirm/(?P<uidb64>.+?)/(?P<token>.+?)$',
        'django.contrib.auth.views.password_reset_confirm',
        {
            'template_name': 'auth/password_reset_confirm.html',
            'post_reset_redirect': reverse_lazy('login'),
        },
        name='password_reset_confirm'),

    url(r'^register$', RegisterView.as_view(), name='register'),

    # topic
    url(r'^list/topics', forum.views.topics.TopicListView.as_view(), name='topic_list'),
    url(r'^t/(?P<id>\d+)$', forum.views.topics.show, name='topic'),
    url(r'^t/(?P<id>\d+)/edit$', forum.views.topics.EditView.as_view(), name='topic_edit'),
    url(r'^t/(?P<id>\d+)/delete$', forum.views.topics.DeleteTopicView.as_view(), name='topic_delete'),
    url(r'^t/(?P<id>\d+)/delete_reply$', forum.views.topics.DeleteTopicReplyView.as_view(), name='topic_delete_reply'),
    url(r'^favourite/(?P<id>\d+)$', forum.views.topics.FavouriteView.as_view(), name='topic_favourite'),
    url(r'^unfavourite/(?P<id>\d+)$', forum.views.topics.UnfavouriteView.as_view(), name='topic_unfavourite'),
    url(r'^reply/(?P<id>\d+)$', forum.views.topics.reply, name='reply'),
    url(r'^new/(?P<slug>\w+)$', forum.views.topics.NewView.as_view(), name='new_topic'),

    # user
    url(r'^member/(?P<name>\w+)$', forum.views.users.home, name='user'),
    url(r'^member/(?P<name>\w+)/topics$', forum.views.users.TopicsView.as_view(), name='user_topics'),
    url(r'^member/(?P<name>\w+)/replies$', forum.views.users.RepliesView.as_view(), name='user_replies'),
    url(r'^member/(?P<name>\w+)/update$', forum.views.users.UpdateProfileView.as_view(), name='user_update'),
    url(r'^follow/(?P<name>\w+)', forum.views.users.FollowView.as_view(), name='follow'),
    url(r'^unfollow/(?P<name>\w+)', forum.views.users.UnfollowView.as_view(), name='unfollow'),

    url(r'^my/topics$', forum.views.users.MyTopicsView.as_view(), name='my_topics'),
    url(r'^my/nodes$', forum.views.users.MyNodesView.as_view(), name='my_nodes'),
    url(r'^my/followings$', forum.views.users.MyFollowingsView.as_view(), name='my_followings'),
    url(r'^my/notifications$', forum.views.users.NotificationView.as_view(), name='notifications'),

    # node
    url(r'^go/(?P<slug>\w+)$', forum.views.nodes.show, name='node'),
    url(r'^node/collect/(?P<slug>\w+)$', forum.views.nodes.CollectView.as_view(), name='node_collect'),
    url(r'^node/uncollect/(?P<slug>\w+)$', forum.views.nodes.UncollectView.as_view(), name='node_uncollect'),

    # blog
    url(r'^blog/(?P<id>\d+)$', forum.views.blogs.BlogView.as_view(), name='blog'),
    url(r'^blog/(?P<id>\d+)/delete$', forum.views.blogs.DeleteBlogView.as_view(), name='blog_delete'),
    url(r'^blog/(?P<id>\d+)/edit$', forum.views.blogs.UpdateBlogView.as_view(), name='blog_edit'),
    url(r'^blog/(?P<id>\d+)/comment$', forum.views.blogs.comment, name='comment'),
    url(r'^blog/list$', forum.views.blogs.BlogListView.as_view(), name='blog_list'),
    url(r'^stick/(?P<id>\w+)$', forum.views.blogs.StickView.as_view(), name='blog_stick'),
    url(r'^unstick/(?P<id>\w+)$', forum.views.blogs.UnstickView.as_view(), name='blog_unstick'),
    url(r'^blog/(?P<id>\d+)/delete_comment$', forum.views.blogs.DeleteCommentView.as_view(), name='blog_delete_comment'),
    url(r'^blogs/new$', forum.views.blogs.NewBlogView.as_view(), name='new_blog'),

    # other
    url(r'^events$', forum.views.events.EventsView.as_view(), name='events'),
    url(r'^forex$', forum.views.forex.ForexView.as_view(), name='forex'),

    url(r'^proxy/(?P<url>.*)', forum.views.root.proxy, name='proxy'),
    url(r'^upload_pic$', forum.views.root.UploadPicView.as_view(), name='upload_pic'),

)