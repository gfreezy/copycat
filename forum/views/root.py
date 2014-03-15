from django.shortcuts import render
from django.contrib.auth.models import User
from forum.models import Node, Topic, Reply, Plane


def index(request):
    template_variables = {}
    template_variables["status_counter"] = {
        "users": User.objects.count(),
        "nodes": Node.objects.count(),
        "topics": Topic.objects.count(),
        "replies": Reply.objects.count(),
    }
    template_variables["topics"] = Topic.hot()
    template_variables["planes"] = Plane.objects.all()
    template_variables["hot_nodes"] = Node.objects.all()
    template_variables["active_page"] = "topic"
    return render(request, 'common/index.html', template_variables)
