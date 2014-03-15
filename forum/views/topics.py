#coding: utf8
from django import forms
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
from forum.models import Topic, Node
from lib.login_required_mixin import LoginRequiredMixin


def show(request, id):
    t = get_object_or_404(Topic, pk=id)
    page_number = request.GET.get('page')
    paginator = Paginator(t.reply_set.all(), 20)
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver last page.
        page = paginator.page(paginator.num_pages)
    except EmptyPage:
        raise Http404
    return render(request, 'topics/show.html', {
        'topic': t,
        'page': page,
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


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title', 'content']


class New(CreateView, LoginRequiredMixin):
    template_name = 'topics/new.html'
    model = Topic
    form_class = TopicForm

    def form_valid(self, form):
        slug = self.kwargs['slug']
        node = get_object_or_404(Node, slug=slug)
        form.instance.author = self.request.user
        form.instance.node = node
        messages.success(self.request, '主题创建成功')
        return super(New, self).form_valid(form)
