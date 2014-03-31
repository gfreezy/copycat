from forum.models import Node, Topic, User, CentralBank


def global_variables(request):
    return {
        'hot_nodes': Node.hot(),
        'hot_topics': Topic.hot(),
        'hot_users': User.hot(),
        'latest_topics': Topic.objects.order_by('-id')[:10],
        'central_banks': CentralBank.objects.all(),
    }