# coding: utf8
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.list import ListView
from forum.models import Blog
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages


class BlogView(ListView):
    template_name = 'blogs/show.html'
    http_method_names = ['get']
    model = Blog
    paginate_by = 6

    def get(self, request, *args, **kwargs):
        id = self.kwargs.get('id')
        self.blog = get_object_or_404(Blog, pk=id)
        return super(BlogView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        return self.blog.comment_set.all()

    def get_context_data(self, **kwargs):
        self.blog.hit()
        if self.request.user.is_authenticated():
            self.request.user.clear_notifications_with_blog(self.blog)
        ctx = super(BlogView,self).get_context_data(**kwargs)
        ctx['blog'] = self.blog
        ctx['request'] = self.request
        return ctx


class BlogListView(ListView):
    template_name = 'blogs/list.html'
    http_method_names = ['get']
    model = Blog
    paginate_by = 20

    def get_queryset(self):
        return Blog.objects.order_by('-id')


@require_POST
@login_required
def comment(request, id):
    b = get_object_or_404(Blog, pk=id)
    content = request.POST.get('content', '').strip()
    if not content:
        messages.error(request, '评论不能为空')
        return redirect(b)

    messages.success(request, '评论成功')
    b.new_comment(content=content, author=request.user)
    return redirect(b)