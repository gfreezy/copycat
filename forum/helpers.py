#coding: utf8
import re
import pytz
import django.utils.timezone
import bleach
import jinja2
from datetime import datetime, timedelta
from jingo import register, env
from jinja2.utils import Markup
from markdown import markdown as markdown_
from django.template.loader import render_to_string
from django.conf import settings
from urllib import urlencode
from urlparse import parse_qs, urlsplit, urlunsplit


if settings.TIME_ZONE:
    local_tzinfo = pytz.timezone(settings.TIME_ZONE)
else:
    local_tzinfo = pytz.utc


def rename(name):
    def _(f):
        f.__name__ = name
        return f
    return _


def localtime(value):
    return value.astimezone(local_tzinfo)


def is_naive(value):
    """
    Determines if a given datetime.datetime is naive.

    The logic is described in Python's docs:
    http://docs.python.org/library/datetime.html#datetime.tzinfo
    """
    return value.tzinfo is None or value.tzinfo.utcoffset(value) is None


def template_localtime(value, use_tz=None):
    """
    Checks if value is a datetime and converts it to local time if necessary.

    If use_tz is provided and is not None, that will force the value to
    be converted (or not), overriding the value of settings.USE_TZ.

    This function is designed for use by the template engine.
    """
    should_convert = (isinstance(value, datetime)
        and (settings.USE_TZ if use_tz is None else use_tz)
        and not is_naive(value)
        and getattr(value, 'convert_to_local_time', True))
    return localtime(value) if should_convert else value


@register.filter
def date(d, format='%Y-%m-%d', tz=None):
    local = template_localtime(d, tz)
    if isinstance(format, unicode):
        format = format.encode('utf8')
    return local.strftime(format).decode('utf8')


@register.filter
@rename('datetime')
def datetime_(d, format='%Y-%m-%d %H:%M:%S', tz=None):
    local = template_localtime(d, tz)
    if isinstance(format, unicode):
        format = format.encode('utf8')
    return local.strftime(format).decode('utf8')


@register.filter
def human_date(t):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    now = django.utils.timezone.now()
    if type(t) is int:
        diff = now - datetime.fromtimestamp(t)
    if isinstance(t, datetime):
        diff = now - t

    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return u"刚刚"
        if second_diff < 60:
            return unicode(second_diff) + u" 秒前"
        if second_diff < 120:
            return u"1 分钟前"
        if second_diff < 3600:
            return unicode(second_diff / 60) + u" 分钟前"
        if second_diff < 7200:
            return u"1 小时前"
        if second_diff < 86400:
            return unicode(second_diff / 3600) + u" 小时前"
    if day_diff == 1:
        return u"昨天"
    if day_diff < 31:
        return unicode(day_diff) + u" 天前"
    if day_diff < 365:
        return unicode(day_diff/30) + u" 个月前"
    return unicode(day_diff/365) + u" 年前"


def gen_page_list(current_page=1, total_page=1, list_rows=10):
    '''list_rows: 最多显示多少页码'''
    if total_page <= list_rows:
        return range(1, total_page + 1)

    if current_page + list_rows > total_page:
        return range(total_page - list_rows + 1, list_rows + 1)

    return range(current_page, list_rows + 1)


@register.filter
def paginate(page, url_pattern='?page=%s', list_rows=10):
    page_list = gen_page_list(page.number, page.paginator.num_pages, list_rows=10)
    return Markup(render_to_string('helpers/pagination.html', {
        'page': page,
        'url_pattern': url_pattern,
        'page_list': page_list,
    }))


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@register.filter
def content_process(content):
    # render content included gist
    content = re.sub(r'http(s)?:\/\/gist.github.com\/(\d+)(.js)?',
                     r'<script src="http://gist.github.com/\2.js"></script>', content)
    # render sinaimg pictures
    content = re.sub(r'(http:\/\/\w+.sinaimg.cn\/.*?\.(jpg|gif|png))', r'<img src="\1" />', content)
    # render @ mention links
    content = re.sub(r'@(\w+)(\s|)', r'@<a href="/u/\1">\1</a> ', content)
    # render youku videos
    content = re.sub(r'http://v.youku.com/v_show/id_(\w+).html',
                     r'<iframe height=498 width=510 src="http://player.youku.com/embed/\1" frameborder=0 allowfullscreen style="width:100%;max-width:510px;"></iframe>',
                     content)
    content = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') for p in _paragraph_re.split(content))
    return content


@register.filter
def markdown(content):
    if not content:
        return ""
    return markdown_(content, extensions=['codehilite', 'fenced_code'], safe_mode='escape')


@register.filter
def dump_errors(errors):
    t = env.from_string('''
        {% if errors %}
            {% for field_name, field_errors in errors.items() %}
                {% for err in field_errors %}
                <div class="alert alert-error">
                {{ err }}
                </div>
                {%endfor%}
            {% endfor %}
        {% endif %}
    ''')
    return Markup(t.render(dict(errors=errors)))


@register.filter
def dump_messages(messages):
    t = env.from_string('''
        {% if messages %}
            {% for message in messages %}
            <div class="alert {% if message.tags %}alert-{{ message.tags }}{% endif %}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    ''')
    return Markup(t.render(dict(messages=messages)))


@register.filter
def css(field, arg):
    return field.as_widget(attrs={'class': arg})


ALLOWED_TAGS = [
    'a',
    'blockquote',
    'li',
    'ol',
    'p',
    'div',
    'span',
    'ul',
    'br',
    'img',
]

ALLOWED_ATTRIBUTES = {
    '*': ['style'],
    'a': ['href', 'title', 'target'],
    'img': ['src', 'title'],
}

ALLOWED_STYLES = ['font', 'font-weight', 'font-size', 'font-style', 'text-align', 'text-decoration',
                  'line-height', 'width', 'height', 'color']


@register.filter
def sanitize(text):
    return Markup(bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES))


@register.filter
def param(url, **kwargs):
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string)

    for param_name, param_value in kwargs.items():
        query_params[param_name] = [param_value]
    new_query_string = urlencode(query_params, doseq=True)

    return urlunsplit((scheme, netloc, path, new_query_string, fragment))


@register.function(override=False)
def prev_day(date):
    delta = timedelta(days=1)
    return date - delta


@register.function(override=False)
def next_day(date):
    delta = timedelta(days=1)
    return date + delta