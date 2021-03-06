#coding: utf8
import re
import os
import math
from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.db import models, transaction, connection
from django.core.urlresolvers import reverse
from django.utils import timezone
from sky_thumbnails.fields import EnhancedImageField
from jsonfield import JSONField
from django.core import exceptions


METHION_REGEXP = re.compile(r"@(?P<username>\w+)(\s|$)", re.I)


def find_mentions(content):
    names = [m.group("username") for m in METHION_REGEXP.finditer(content)]
    return User.objects.filter(username__in=names)


def filepath(prefix, filename):
    h = str(hash(filename))
    return os.path.join(prefix, h[-2:], h[-4:-2], filename)


class UserManager(BaseUserManager):
    def _create_user(self, username, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set')
        with transaction.atomic():
            email = self.normalize_email(email)
            user = self.model(username=username, email=email,
                              is_staff=is_staff, is_active=True,
                              is_superuser=is_superuser, last_login=now,
                              date_joined=now, **extra_fields)
            user.set_password(password)
            user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        return self._create_user(username, email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        return self._create_user(username, email, password, True, True,
                                 **extra_fields)

    def create_oauth_user(self, provider, uid, access_token, avatar=None):
        # todo: get user name and user avatar
        u = self.create_user(provider+uid)
        u.connect(provider, uid, access_token)
        return u


class User(AbstractUser):
    avatar = EnhancedImageField(
        blank=True,
        default='default/avatar.png',
        upload_to=lambda _, filename: filepath('user', filename),
        thumbnails={
            'small': dict(size=(48, 48), sharpen=True),
            'medium': dict(size=(73, 73), sharpen=True),
        }
    )
    gold = models.IntegerField(default=2000, help_text='gold')
    profile = models.TextField(blank=True, help_text='user profile')
    n_favourites = models.IntegerField(default=0, editable=False, help_text='topic favourites')
    n_followings = models.IntegerField(default=0, editable=False, help_text='user followings')
    n_collects = models.IntegerField(default=0, editable=False, help_text='node collects')

    followers = models.ManyToManyField('self', through='Follow', symmetrical=False, related_name='followings',
                                       related_query_name='user')
    favourite_topics = models.ManyToManyField('Topic', through='Favourite',
                                              related_name='favouriting_users',
                                              related_query_name='user')

    last_active_time = models.DateTimeField(auto_now=True, db_index=True)
    objects = UserManager()

    @classmethod
    def hot(cls, n=6):
        return cls.objects.order_by('-last_active_time')[:n]

    @classmethod
    def from_oauth(cls, provider, uid, access_token, avatar=None):
        try:
            u = SocialAccount.objects.get(provider=provider, uid=uid)
            return u.user
        except exceptions.ObjectDoesNotExist:
            return cls.objects.create_oauth_user(provider, uid, access_token, avatar)

    def get_absolute_url(self):
        return reverse('user', kwargs={'name': self.username})

    def update_active_time(self):
        self.last_active_time = timezone.now()
        self.save()

    def favourite(self, topic):
        if topic._favourite(self):
            self.n_favourites += 1
            self.save()
            topic_author = topic.author
            topic_author.gold += 2 * int(math.ceil(math.log10(self.gold + topic.age)))
            topic_author.save()
            return True
        return False

    def unfavourite(self, topic):
        if topic._unfavourite(self):
            self.n_favourites -= 1
            self.save()
            return True
        return False

    def follow(self, u):
        if not self.is_following(u) and u != self:
            Follow.objects.create(target=u, by=self)
            self.n_followings += 1
            self.save()
            Notification.notify_follow(self, u)
            return True
        return False

    def unfollow(self, u):
        if self.is_following(u):
            Follow.objects.filter(target=u, by=self).delete()
            self.n_followings -= 1
            self.save()
            return True
        return False

    def is_following(self, u):
        return self.followings.filter(id=u.id).exists()

    def followed_by(self, u):
        return Follow.objects.filter(by=u, target=self).exists()

    def following_users_topics(self):
        following_user_ids = self.followings.values_list('id', flat=True)
        return Topic.objects.filter(author_id__in=following_user_ids).order_by('-id')

    def collected_nodes_topics(self):
        node_ids = self.collected_nodes.values_list('id', flat=True)
        return Topic.objects.filter(node_id__in=node_ids).order_by('-id')

    def collect(self, node):
        if not node.collected_by(self):
            Collect.objects.create(node=node, author=self)
            self.n_collects += 1
            self.save()
            return True
        return False

    def uncollect(self, node):
        if node.collected_by(self):
            Collect.objects.filter(author=self, node=node).delete()
            self.n_collects -= 1
            self.save()
            return True
        return False

    def has_collected(self, node):
        return node.collected_by(self)

    def notifications(self):
        return Notification.notifications_for(self)

    def unread_notifications(self):
        return Notification.unread_notifications_for(self)

    def read_notifications(self):
        return Notification.read_notifications_for(self)

    def clear_notifications_with_topic(self, topic):
        return Notification._clear_user_notifications_with_topic(topic, self)

    def clear_notifications_with_blog(self, blog):
        return Notification._clear_user_notifications_with_blog(blog, self)

    def clear_notifications_with_member(self, member):
        return Notification._clear_user_notifications_with_member(member, self)

    def mark_all_as_read(self):
        return Notification.mark_all_as_read_for(self)

    def connect(self, provider, uid, access_token):
        s = SocialAccount.objects.get_or_create(user=self, provider=provider, uid=uid)[0]
        s.access_token = access_token
        s.save()

    def disconnect(self, provider):
        SocialAccount.objects.filter(user=self, provider=provider).delete()

    def connected_to(self, provider):
        return SocialAccount.objects.filter(user=self, provider=provider).exists()


class SocialAccount(models.Model):
    class Meta:
        index_together = (('provider', 'uid'), ('user', 'provider', 'uid'))

    uid = models.CharField(max_length=200)
    provider = models.CharField(max_length=100)
    access_token = models.CharField(max_length=200)
    user = models.ForeignKey(User)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)


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
        upload_to=lambda _, filename: filepath('node', filename),
        blank=True,
        process_source=dict(size=(73, 73), sharpen=True, upscale=True),
    )

    plane = models.ForeignKey(Plane)
    collecting_users = models.ManyToManyField(User, through='Collect',
                                              related_name='collected_nodes',
                                              related_query_name='node')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)

    def __unicode__(self):
        return '<Node:%s %s>' % (self.id, self.name)

    @classmethod
    def hot(cls, number=10):
        c = connection.cursor()
        c.execute('select node_id, count(id) as c from forum_topic where created >= %s '
                  'group by node_id order by c desc limit %s', [timezone.now().date(), number])
        hot_node_ids = [id for id, _ in c.fetchall()]
        return cls.objects.filter(id__in=hot_node_ids)

    def get_absolute_url(self):
        return reverse('node', kwargs={'slug': self.slug})

    def collected_by(self, u):
        return Collect.objects.filter(author=u, node=self).exists()


class Topic(models.Model):
    title = models.CharField(max_length=200, default='')
    content = models.TextField(default='')
    n_hits = models.IntegerField(default=0, editable=False)
    n_favourites = models.IntegerField(default=0, editable=False)
    n_replies = models.IntegerField(default=0, editable=False)

    node = models.ForeignKey(Node)
    author = models.ForeignKey(User)

    last_active_time = models.DateTimeField(auto_now=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)

    def __unicode__(self):
        return '<Topic:%s %s>' % (self.id, self.title)

    @classmethod
    def hot(cls, number=10):
        return cls.objects.order_by('-last_active_time')[:number]

    @property
    def age(self):
        return (timezone.now() - self.created).days

    def hit(self):
        self.n_hits += 1
        self.save()
        return self.n_hits

    def get_absolute_url(self):
        return reverse('topic', kwargs=dict(id=self.id))

    def new_reply(self, content, author):
        with transaction.atomic():
            reply = self.reply_set.create(content=content, author=author)
            self.n_replies += 1
            self.last_active_time = reply.created
            self.save()

            # A的话题被B首次回复，A的金币加 2∗log10(B的金币值+帖子发表距今的天数)
            if Reply.objects.filter(topic=self, author=author).count() == 1:
                topic_author = self.author
                topic_author.gold += 2 * int(math.ceil(math.log10(author.gold+self.age)))
                topic_author.save()

            author.update_active_time()
            author.gold -= 2
            author.save()

            if self.author != author:
                # Not create notification for self's reply
                Notification.notify_reply(author, self.author, self, reply)

            for u in find_mentions(content):
                # Not create notification for mention self
                if u == author:
                    continue
                Notification.notify_mention(author, u, self, reply)

        return reply

    def _favourite(self, by):
        if not self.favourited_by(by):
            with transaction.atomic():
                fav = Favourite.objects.create(topic=self, author=by)
                self.n_favourites += 1
                self.save()
            return True
        return False

    def _unfavourite(self, by):
        if self.favourited_by(by):
            with transaction.atomic():
                Favourite.objects.filter(topic=self, author=by).delete()
                self.n_favourites -= 1
                self.save()
            return True
        return False

    def favourited_by(self, by):
        return Favourite.objects.filter(topic=self, author=by).exists()

    def created_by(self, by):
        return self.author == by


class Reply(models.Model):
    content = models.TextField()

    author = models.ForeignKey(User)
    topic = models.ForeignKey(Topic)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)

    def __unicode__(self):
        return '<Reply:%s Topic:%s>' % (self.id, self.topic.id)


class Favourite(models.Model):
    topic = models.ForeignKey(Topic, related_name='+')
    author = models.ForeignKey(User, related_name='+')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)


class Follow(models.Model):
    target = models.ForeignKey(User, related_name='+')
    by = models.ForeignKey(User, related_name='+')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)


class Collect(models.Model):
    node = models.ForeignKey(Node, related_name='+')
    author = models.ForeignKey(User, related_name='+')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)


class Notification(models.Model):
    class Meta:
        index_together = (('receiver', 'status', 'id'), )
    MENTION = 0
    REPLY = 1
    FOLLOW = 2
    COMMENT = 3
    MENTION_IN_COMMENT = 4
    READ = 3
    UNREAD = 4

    sender = models.ForeignKey(User, related_name='+')
    receiver = models.ForeignKey(User, related_name='+')
    kind = models.IntegerField(choices=((MENTION, 'mention'), (REPLY, 'reply'),
                                        (FOLLOW, 'follow'), (COMMENT, 'comment'),
                                        (COMMENT, 'comment'), (MENTION_IN_COMMENT, 'menion_in_comment')))
    target_id = models.IntegerField()
    extra = JSONField()
    status = models.IntegerField(choices=((READ, 'read'), (UNREAD, 'read')), default=UNREAD)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)

    @classmethod
    def notify_reply(cls, sender, receiver, topic, reply):
        if sender == receiver:
            raise Exception('cant not send notification to self')
        extra = {
            'reply_id': reply.id,
        }
        if isinstance(topic, Blog):
            kind = cls.COMMENT
        elif isinstance(topic, Topic):
            kind = cls.REPLY
        return cls.objects.create(sender=sender, receiver=receiver, target_id=topic.id, extra=extra, kind=kind)

    @classmethod
    def notify_mention(cls, sender, receiver, target, target_reply):
        if sender == receiver:
            raise Exception('cant not send notification to self')

        extra = {
            'reply_id': target_reply.id,
        }
        if isinstance(target, Blog):
            kind = cls.MENTION_IN_COMMENT
        elif isinstance(target, Topic):
            kind = cls.MENTION
        return cls.objects.create(sender=sender, receiver=receiver, target_id=target.id, extra=extra, kind=kind)

    @classmethod
    def notify_follow(cls, sender, receiver):
        if sender == receiver:
            raise Exception('cant not send notification to self')

        return cls.objects.create(sender=sender, receiver=receiver, target_id=receiver.id, extra={}, kind=cls.FOLLOW)

    @classmethod
    def notifications_for(cls, u):
        return cls.objects.filter(receiver=u).order_by('-status', '-id')

    @classmethod
    def unread_notifications_for(cls, u):
        return cls.objects.filter(receiver=u, status=cls.UNREAD).order_by('-id')

    @classmethod
    def read_notifications_for(cls, u):
        return cls.objects.filter(receiver=u, status=cls.READ).order_by('-id')

    @classmethod
    def count_notifications_for(cls, u):
        return cls.notifications_for(u).count()

    @classmethod
    def count_unread_notifications_for(cls, u):
        return cls.unread_notifications_for(u).count()

    @classmethod
    def count_notifications_for(cls, u):
        return cls.read_notifications_for(u).count()

    @classmethod
    def mark_all_as_read_for(cls, u):
        return cls.unread_notifications_for(u).update(status=cls.READ)

    @classmethod
    def _clear_user_notifications_with_topic(cls, topic, user):
        return cls.objects.filter(target_id=topic.id, receiver=user, status=cls.UNREAD,
                                  kind__in=[cls.REPLY, cls.MENTION]).update(status=cls.READ)
    @classmethod
    def _clear_user_notifications_with_blog(cls, blog, user):
        return cls.objects.filter(target_id=blog.id, receiver=user, status=cls.UNREAD,
                                  kind__in=[cls.COMMENT, cls.MENTION_IN_COMMENT]).update(status=cls.READ)

    @classmethod
    def _clear_user_notifications_with_member(cls, topic, user):
        return cls.objects.filter(target_id=topic.id, receiver=user, status=cls.UNREAD,
                                  kind=cls.FOLLOW).update(status=cls.READ)

    @property
    def topic(self):
        if self.kind not in (self.MENTION, self.REPLY):
            raise Exception('Not implemented')
        return Topic.objects.get(pk=self.target_id)

    @property
    def reply(self):
        if self.kind not in (self.MENTION, self.REPLY):
            raise Exception('Not implemented')
        return Reply.objects.get(pk=self.extra['reply_id'])

    @property
    def blog(self):
        if self.kind not in (self.COMMENT, self.MENTION_IN_COMMENT):
            raise Exception('Not implemented')
        return Blog.objects.get(pk=self.target_id)

    @property
    def comment(self):
        if self.kind not in (self.COMMENT, self.MENTION_IN_COMMENT):
            raise Exception('Not implemented')
        return Comment.objects.get(pk=self.extra['reply_id'])

    def mark_as_read(self):
        self.status = self.READ
        self.save()


class Blog(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    cover = EnhancedImageField(
        upload_to=lambda _, filename: filepath('blog', filename),
        blank=True,
        # default='user/2014/03/5f050d0cd1b9d93b5db499cd6a70e0bf.jpg',
        process_source=dict(size=(733, 412), sharpen=True),
        thumbnails={
            'strip': dict(size=(733, 231), sharpen=True, upscale=True),
            'thumb': dict(size=(550, 412), sharpen=True, upscale=True),
        }
    )
    n_comments = models.IntegerField(default=0, editable=False, db_index=True)
    n_hits = models.IntegerField(default=0, editable=False)

    author = models.ForeignKey(User)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)

    @classmethod
    def recent(cls, n=2):
        return cls.objects.order_by('-id')[:n]

    @classmethod
    def sticks(cls):
        blog_ids = StickBlog.objects.order_by('-id')[:10].values_list('blog_id')
        return cls.objects.filter(id__in=blog_ids)

    @classmethod
    def hot(cls, n=8):
        c = connection.cursor()
        c.execute('select blog_id, count(id) as c from forum_comment where '
                  'created > %s group by blog_id order by c desc limit %s', [timezone.now().date(), n])
        bids = [id for id, _ in c.fetchall()]
        return cls.objects.filter(id__in=bids)

    def __unicode__(self):
        return u'%s %s\t%s' % (self.id, self.created.strftime('%m-%d %H:%M'), self.title)

    def hit(self):
        self.n_hits += 1
        self.save()
        return self.n_hits

    def get_absolute_url(self):
        return reverse('blog', args=[self.id])

    def created_by(self, u):
        return self.author == u

    def new_comment(self, content, author):
        c = self.comment_set.create(content=content, author=author)
        self.n_comments += 1
        self.save()

        author.update_active_time()
        if self.author != author:
            # Not create notification for self's reply
            Notification.notify_reply(author, self.author, self, c)

        for u in find_mentions(content):
            # Not create notification for mention self
            if u == author:
                continue
            Notification.notify_mention(author, u, self, c)

        return c

    def stick(self):
        self.unstick()
        StickBlog.objects.create(blog=self)

    def unstick(self):
        StickBlog.objects.filter(blog=self).delete()

    def sticked(self):
        return StickBlog.objects.filter(blog=self).exists()


class Comment(models.Model):
    content = models.TextField()

    author = models.ForeignKey(User)
    blog = models.ForeignKey(Blog)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)


class StickBlog(models.Model):
    blog = models.ForeignKey(Blog)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)


class EconomicEvent(models.Model):
    time = models.DateTimeField()
    country = models.CharField(max_length=100)
    flag_cur = models.CharField(max_length=20)
    txt_num = models.CharField(max_length=20)
    event = models.CharField(max_length=1000)
    act = models.CharField(max_length=20, blank=True)
    fore = models.CharField(max_length=20, blank=True)
    prev = models.CharField(max_length=20, blank=True)
    ident = models.CharField(unique=True, max_length=32)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)


class ImportEvent(models.Model):
    time = models.DateTimeField()
    currency = models.CharField(max_length=100)
    event = models.CharField(max_length=1000)
    ident = models.CharField(unique=True, max_length=32)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)


class Forex(models.Model):
    time = models.DateTimeField()
    title = models.CharField(max_length=20)
    article = models.TextField(blank=True)
    url = models.URLField()
    ident = models.CharField(unique=True, max_length=32)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)


class CentralBank(models.Model):
    name = models.CharField(max_length=100, unique=True)
    bank = models.CharField(max_length=100)
    url = models.URLField()
    rate = models.CharField(max_length=20)
    next_metting = models.CharField(max_length=200)
    last_changed = models.CharField(max_length=200)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)


class Picture(models.Model):
    pic = EnhancedImageField(
        upload_to=lambda _, filename: filepath('pic', filename),
    )