#coding: utf8
import re
import django.utils.timezone
from datetime import datetime
from jingo import register, env
from jinja2.utils import Markup
from markdown import markdown as markdown_
from django.template.loader import render_to_string


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
            return unicode(second_diff) + u"秒前"
        if second_diff < 120:
            return u"1分钟前"
        if second_diff < 3600:
            return unicode(second_diff / 60) + u"分钟前"
        if second_diff < 7200:
            return u"1小时前"
        if second_diff < 86400:
            return unicode(second_diff / 3600) + u"小时前"
    if day_diff == 1:
        return u"昨天"
    if day_diff < 31:
        return unicode(day_diff) + u"天前"
    if day_diff < 365:
        return unicode(day_diff/30) + u"个月前"
    return unicode(day_diff/365) + u"年前"


def gen_page_list(current_page=1, total_page=1, list_rows=10):
    '''list_rows: 最多显示多少页码'''
    if (total_page <= list_rows):
        return range(1, total_page + 1)

    if (current_page + list_rows > total_page):
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
        <div class="errors alert alert-error">
            {% for field_errors in errors.values() %}
                {% for err in field_errors %}
                <div>{{ err }}</div>
                {%endfor%}
            {% endfor %}
        </div>
        {% endif %}
    ''')
    return Markup(t.render(dict(errors=errors)))


@register.filter
def dump_messages(messages):
    t = env.from_string('''
        {% if messages %}
        <div class="messages">
            {% for message in messages %}
            <div class="alert {% if message.tags %}alert-{{ message.tags }}{% endif %}">{{ message }}</div>
            {% endfor %}
        </div>
        {% endif %}
    ''')
    return Markup(t.render(dict(messages=messages)))


@register.filter
def css(field, arg):
    return field.as_widget(attrs={'class': arg})
