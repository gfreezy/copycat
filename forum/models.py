#coding: utf8
from django.contrib.auth.models import User
from django.db import models, transaction
from django.core.urlresolvers import reverse
from sky_thumbnails.fields import EnhancedImageField


def create_user(*args, **kwargs):
    with transaction.atomic():
        u = User.objects.create_user(*args, **kwargs)
        Profile.objects.create(user=u)
    return u


class Plane(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=20, unique=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)

    def __unicode__(self):
        return '<Plane:%s %s>' % (self.id, self.name)

    def get_absolute_url(self):
        return reverse('plane', kwargs={'slug': self.slug})


class Node(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=20, unique=True)
    desc = models.TextField(blank=True)
    pic = EnhancedImageField(
        upload_to='node/%Y/%m',
        blank=True,
        process_source=dict(size=(73, 73), sharpen=True, upscale=True),
    )

    plane = models.ForeignKey(Plane)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)

    def __unicode__(self):
        return '<Node:%s %s>' % (self.id, self.name)

    def get_absolute_url(self):
        return reverse('node', kwargs={'slug': self.slug})


class Profile(models.Model):
    user = models.OneToOneField(User)
    avatar = EnhancedImageField(
        blank=True,
        default='user/2014/03/5f050d0cd1b9d93b5db499cd6a70e0bf.jpg',
        upload_to='user/%Y/%m',
        thumbnails={
            'small': dict(size=(48, 48), sharpen=True),
            'medium': dict(size=(73, 73), sharpen=True),
        }
    )


class Stats(models.Model):
    user = models.OneToOneField(User)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)


class Topic(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    hits = models.IntegerField(default=0, editable=False)
    reply_count = models.IntegerField(default=0, editable=False)

    node = models.ForeignKey(Node)
    author = models.ForeignKey(User)

    last_active_time = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)

    def __unicode__(self):
        return '<Topic:%s %s>' % (self.id, self.title)

    @classmethod
    def hot(cls):
        return cls.objects.order_by('-last_active_time')[:20]

    def get_absolute_url(self):
        return reverse('topic', kwargs=dict(id=self.id))

    def new_reply(self, content, author):
        with transaction.atomic():
            reply = self.reply_set.create(content=content, author=author)
            self.reply_count = models.F('reply_count') + 1
            self.last_active_time = reply.created
            self.save()
        return reply


class Reply(models.Model):
    content = models.TextField()

    author = models.ForeignKey(User)
    topic = models.ForeignKey(Topic)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)

    def __unicode__(self):
        return '<Reply:%s Topic:%s>' % (self.id, self.topic.id)
