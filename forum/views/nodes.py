from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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
