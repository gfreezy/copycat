from django.contrib import admin
from forum.models import Plane, Node, Blog, User

admin.site.register(User)
admin.site.register(Plane)
admin.site.register(Node)
admin.site.register(Blog)