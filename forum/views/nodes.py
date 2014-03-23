from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import View
from braces.views import LoginRequiredMixin, JSONResponseMixin
from forum.models import Node


def show(request, slug):
    node = get_object_or_404(Node, slug=slug)
    page_number = request.GET.get('page')
    paginator = Paginator(node.topic_set.all(), 20)
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver last page.
        page = paginator.page(paginator.num_pages)
    except EmptyPage:
        raise Http404
    return render(request, 'nodes/list.html', {
        'node': node,
        'page': page,
    })


class CollectView(View, LoginRequiredMixin, JSONResponseMixin):
    http_method_names = ['post']

    def post(self, request, slug):
        node = get_object_or_404(Node, slug=slug)
        if node.collected_by(request.user):
            return self.render_json_response({
                'errors': [
                    {'message': 'already collected'}
                ]
            }, 400)
        request.user.collect(node)
        return self.render_json_response({
            'collects': request.user.n_collects
        })


class UncollectView(View, LoginRequiredMixin, JSONResponseMixin):
    http_method_names = ['post']

    def post(self, request, slug):
        node = get_object_or_404(Node, slug=slug)
        if not node.collected_by(request.user):
            return self.render_json_response({
                'errors': [
                    {'message': 'not collected'}
                ]
            }, 400)
        request.user.uncollect(node)
        return self.render_json_response({
            'collects': request.user.n_collects
        })