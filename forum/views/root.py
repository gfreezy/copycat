from django.shortcuts import render
from forum.models import Node, Topic, Plane, User, Reply


def index(request):
    return render(request, 'common/index.html')