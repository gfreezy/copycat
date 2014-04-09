#coding: utf8
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView
from django.views.generic import View
from braces.views import LoginRequiredMixin, JSONResponseMixin
from django.core.urlresolvers import reverse
from forum.models import Topic, Reply, User, Notification


def home(request, name):
    u = get_object_or_404(User, username=name)
    user = request.user
    if user.is_authenticated():
        user.clear_notifications_with_member(u)
    return render(request, 'users/home.html', {
        'owner': u,
        'tab': 'home',
    })


class UpdateProfileView(UpdateView):
    fields = ['username', 'email', 'profile', 'avatar']
    template_name = 'users/update_profile.html'
    model = User

    def get_object(self, queryset=None):
        u = get_object_or_404(User, username=self.kwargs.get('name'))
        return u


class TopicsView(ListView):
    template_name = 'users/topics.html'
    http_method_names = ['get']
    model = Topic
    paginate_by = 20

    def get_queryset(self):
        username = self.kwargs.get('name')
        self.user = get_object_or_404(User, username=username)
        return self.user.topic_set.all()

    def get_context_data(self, **kwargs):
        context = {}
        context.update(kwargs)
        context['owner'] = self.user
        return super(TopicsView, self).get_context_data(**context)


class RepliesView(ListView):
    template_name = 'users/replies.html'
    http_method_names = ['get']
    model = Reply
    paginate_by = 20

    def get_queryset(self):
        username = self.kwargs.get('name')
        self.user = get_object_or_404(User, username=username)
        return self.user.reply_set.all()

    def get_context_data(self, **kwargs):
        context = {}
        context.update(kwargs)
        context['owner'] = self.user
        return super(RepliesView, self).get_context_data(**context)


class MyTopicsView(LoginRequiredMixin, ListView):
    template_name = 'users/my_topics.html'
    http_method_names = ['get']
    model = Topic
    paginate_by = 20

    def get_queryset(self):
        topics = self.request.user.favourite_topics.order_by('-id')
        return topics


class MyNodesView(LoginRequiredMixin, ListView):
    template_name = 'users/my_nodes.html'
    http_method_names = ['get']
    model = Topic
    paginate_by = 20

    def get_queryset(self):
        topics = self.request.user.collected_nodes_topics()
        return topics


class MyFollowingsView(LoginRequiredMixin, ListView):
    template_name = 'users/my_followings.html'
    http_method_names = ['get']
    model = Topic
    paginate_by = 20

    def get_queryset(self):
        topics = self.request.user.following_users_topics()
        return topics


class NotificationView(LoginRequiredMixin, ListView):
    template_name = 'users/notifications.html'
    http_method_names = ['get', 'post']
    model = Notification
    paginate_by = 20

    def get_queryset(self):
        notis = self.request.user.unread_notifications()
        return notis

    def post(self, request):
        request.user.mark_all_as_read()
        return redirect(reverse('notifications'))


class FollowView(LoginRequiredMixin, JSONResponseMixin, View):
    http_method_names = ['post']

    def post(self, request, name):
        u = get_object_or_404(User, username=name)
        if request.user.is_following(u):
            return self.render_json_response({
                'errors': [
                    {'message': 'already followed'}
                ]
            }, 400)
        request.user.follow(u)
        return self.render_json_response({
            'followings': request.user.n_followings
        })


class UnfollowView(LoginRequiredMixin, JSONResponseMixin, View):
    http_method_names = ['post']

    def post(self, request, name):
        u = get_object_or_404(User, username=name)
        if not request.user.is_following(u):
            return self.render_json_response({
                'errors': [
                    {'message': 'not following'}
                ]
            }, 400)
        request.user.unfollow(u)
        return self.render_json_response({
            'followings': request.user.n_followings
        })