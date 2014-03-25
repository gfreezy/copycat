from django.shortcuts import render
from forum.models import Node, Topic, Plane, User, Reply, Blog


def index(request):
    hot_topics = Topic.hot()
    new_topics = Topic.objects.order_by('-id')[:10]
    blogs = Blog.recent()
    stick_blogs = Blog.sticks()
    hot_nodes = Node.hot()
    return render(request, 'common/index.html', {
        'hot': hot_topics,
        'new': new_topics,
        'blogs': blogs,
        'sticks': stick_blogs,
        'hot_nodes': hot_nodes,
        'tab': 'index',
    })