#coding: utf8
import django.contrib.auth.views
import forum.views
from socialoauth import SocialSites
from django.conf import settings
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django import forms
from django.shortcuts import redirect
from braces.views import AnonymousRequiredMixin
from forum.models import User
from forum.views.helpers import login_user


class AuthenticationForm(django.contrib.auth.views.AuthenticationForm):
    error_messages = {
        'invalid_login': "用户名或密码错误",
        'inactive': "帐号未激活",
    }
    username = forms.CharField(max_length=254, error_messages={
        'required': '用户名不能为空'
    })
    password = forms.CharField(label="密码", widget=forms.PasswordInput, error_messages={
        'required': '密码不能为空'
    })


class RegisterForm(forms.Form):
    error_messages = {
        'password_mismatch': '密码不一致',
        'username_exists': '用户名已存在',
        'email_exists': '邮箱已存在',
    }
    username = forms.CharField(label="用户名", initial='', max_length=10, error_messages={
        'required': '用户名不能为空', 'max_length': '用户名不得多于10个字符'})
    email = forms.EmailField(label="E-mail", initial='', error_messages={'required': 'E-mail不能为空'})
    password1 = forms.CharField(label="密码", min_length=4, widget=forms.PasswordInput, error_messages={
        'required': '', 'min_length': ''})
    password2 = forms.CharField(label="密码(确认)", min_length=4, widget=forms.PasswordInput, error_messages={
        'required': '密码不能为空', 'min_length': '密码不少于4个字符'})

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).count():
            raise forms.ValidationError(self.error_messages['username_exists'])
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).count():
            raise forms.ValidationError(self.error_messages['email_exists'])
        return email


class RegisterView(AnonymousRequiredMixin, FormView):
    authenticated_redirect_url = reverse_lazy('index')
    template_name = 'auth/register.html'
    form_class = RegisterForm

    def get_success_url(self):
        return reverse_lazy('index')

    def form_valid(self, form):
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password2'])
        user = authenticate(username=user.username, password=form.cleaned_data['password2'])
        login(self.request, user)
        messages.success(self.request, u'注册成功，欢迎加入,%s' % user.username)
        return super(RegisterView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super(RegisterView, self).get_context_data(**kwargs)
        ctx['social_sites'] = forum.views.social_sites
        return ctx


def oauth(request, provider):
    code = request.GET.get('code')
    if not code:
        # 认证返回的params中没有code，肯定出错了
        # 重定向到某处，再做处理
        raise

    social_sites = SocialSites(settings.SOCIALOAUTH_SITES)
    s = social_sites.get_site_object_by_name(provider)

    # 用code去换取认证的access_token
    s.get_access_token(code)
    u = User.from_oauth(s.name, s.uid, s.access_token, s.avatar)
    login_user(request, u)
    return redirect('index')
