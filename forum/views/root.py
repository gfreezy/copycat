import requests
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import View
from forum.models import Node, Topic, Blog, EconomicEvent, Picture
from braces.views import JSONResponseMixin, LoginRequiredMixin


def index(request):
    hot_topics = Topic.hot()
    new_topics = Topic.objects.order_by('-id')[:10]
    recent_blogs = Blog.recent(8)
    stick_blogs = Blog.sticks()
    hot_blogs = Blog.hot(2)
    hot_nodes = Node.hot()
    return render(request, 'common/index.html', {
        'hot': hot_topics,
        'new': new_topics,
        'recent_blogs': recent_blogs,
        'hot_blogs': hot_blogs,
        'sticks': stick_blogs,
        'hot_nodes': hot_nodes,
        'recent_events': EconomicEvent.objects.order_by('-time')[:10],
        'tab': 'index',
    })


def proxy(request, url):
    res = requests.get(url)
    return HttpResponse(content=res.content, status=res.status_code, content_type=res.headers['Content-Type'])


class UploadPicView(LoginRequiredMixin, JSONResponseMixin, View):
    http_method_names = ['post']

    def post(self, request):
        pic = request.FILES.get('pic')
        p = Picture.objects.create(pic=pic)

        return self.render_json_response({
            'url': p.pic.url,
        })