#coding: utf8
from django import forms
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
from django.views.generic.base import View, TemplateView
from forum.models import Topic, Node, Plane, User, Reply
from braces.views import LoginRequiredMixin, JSONResponseMixin


class TopicForm(forms.ModelForm):
    title = forms.CharField(initial='', max_length=200, error_messages={
        'required': '主题不能为空',
        'max_length': '主题不能超过200个字符',
    })
    content = forms.CharField(initial='', widget=forms.Textarea(), error_messages={
        'required': '正文不能为空'
    })

    class Meta:
        model = Topic
        fields = ['title', 'content']


class TopicListView(TemplateView):
    template_name = 'topics/list.html'
    http_method_names = ['get']

    def get_context_data(self, **kwargs):
        ctx = {
            'hot_topics': Topic.hot(),
            'hot_nodes': Node.hot(),
            'total_users': User.objects.count(),
            'total_topics': User.objects.count(),
            'total_nodes': Node.objects.count(),
            'total_replies': Reply.objects.count(),
            'planes': Plane.objects.all(),
            'tab': 'forum',
        }
        return ctx


def show(request, id):
    t = get_object_or_404(Topic, pk=id)
    user = request.user
    if user.is_authenticated():
        user.clear_notifications_with_topic(t)
    page_number = request.GET.get('page')
    paginator = Paginator(t.reply_set.all(), 20)
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver last page.
        page = paginator.page(paginator.num_pages)
        # incr pv
        t.hit()
    except EmptyPage:
        raise Http404
    return render(request, 'topics/show.html', {
        'topic': t,
        'page': page,
        'request': request,
    })


class FavouriteView(View, LoginRequiredMixin, JSONResponseMixin):
    http_method_names = ['post']
    def post(self, request, id):
        t = get_object_or_404(Topic, pk=id)
        if t.created_by(request.user):
            return self.render_json_response({
                'errors': [
                    {'message': 'can not fav self\'s topic'}
                ]
            }, 400)
        if t.favourited_by(request.user):
            return self.render_json_response({
                'errors': [
                    {'message': 'already favourited'}
                ]
            }, 400)
        request.user.favourite(t)
        return self.render_json_response({
            'favourites': t.n_favourites
        })


class UnfavouriteView(View, LoginRequiredMixin, JSONResponseMixin):
    http_method_names = ['post']
    def post(self, request, id):
        t = get_object_or_404(Topic, pk=id)
        if not t.favourited_by(request.user):
            return self.render_json_response({
                'errors': [
                    {'message': 'not favourited'}
                ]
            }, 400)
        request.user.unfavourite(t)
        return self.render_json_response({
            'favourites': t.n_favourites
        })


@require_POST
@login_required
def reply(request, id):
    t = get_object_or_404(Topic, pk=id)
    content = request.POST.get('content', '').strip()
    if not content:
        messages.error(request, '回复不能为空')
        return redirect(t)

    messages.success(request, '回复成功')
    t.new_reply(content=content, author=request.user)
    return redirect(t)


class NewView(LoginRequiredMixin, CreateView):
    template_name = 'topics/new.html'
    model = Topic
    form_class = TopicForm


    def form_valid(self, form):
        slug = self.kwargs['slug']
        node = get_object_or_404(Node, slug=slug)
        form.instance.author = self.request.user
        form.instance.node = node
        messages.success(self.request, '主题创建成功')
        return super(NewView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        node = get_object_or_404(Node, slug=self.kwargs['slug'])
        ctx = super(NewView, self).get_context_data(**kwargs)
        ctx['node'] = node
        return ctx


