#coding:utf-8
import sys
import json
import random
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib import auth
from django.contrib.auth.models import User
from DjangoCaptcha import Captcha
from django.conf import settings
from mysite.comm import *
reload(sys)
sys.setdefaultencoding('utf-8')

def captcha(request):
    figures = [0,1,2,3,4,5,6,7,8,9]
    #figures = [chr(i) for i in range(97,123)]
    ca =  Captcha(request)
    ca.words = [''.join([str(random.sample(figures,1)[0]) for i in range(0,4)])]
    #ca.type = 'number' #数学运算
    ca.type = 'word'    #字符串
    ca.img_width = 80
    ca.img_height = 20
    return ca.display()

#server
def login_required(func):
    """sso server端登录装饰器"""
    def _deco(request, *args, **kwargs):
        sso_token = request.COOKIES.get('sso_token','')
        username = request.user.username
        login_url = '%s?back=%s' % (settings.LOGIN_URL, request.get_raw_uri())
        if not username and not sso_token:
            return HttpResponseRedirect(login_url)
        elif not username and sso_token:
            url = "%s?token=%s" % (settings.GET_USER_URL, sso_token)
            ret, err = request_get(url)
            if err: return HttpResponseRedirect(login_url)
            sso_dict = ret.json()
            if sso_dict.has_key('error'): return HttpResponseRedirect(login_url)
            return HttpResponseRedirect('/sso/login')
        return func(request, *args, **kwargs)
    return _deco

##client
#def login_required(func):
#    """sso client端登录装饰器"""
#    def _deco(request, *args, **kwargs):
#        sso_token = request.COOKIES.get('sso_token','')
#        user = request.user
#        login_url = '%s?back=%s' % (settings.LOGIN_URL, request.get_raw_uri())
#        if not user.username and not sso_token:
#            return HttpResponseRedirect(login_url)
#        elif not user.username and sso_token:
#            url = "%s?token=%s" % (settings.GET_USER_URL, sso_token)
#            ret, err = request_get(url)
#            if err: return HttpResponseRedirect(login_url)
#            sso_dict = ret.json()
#            if sso_dict.has_key('error'): return HttpResponseRedirect(login_url)
#            user_dict = {'email':sso_dict['email'], 'last_name':sso_dict['cn']}
#            User.objects.update_or_create(username=sso_dict['username'], defaults=user_dict)
#            user = User.objects.get(username=sso_dict['username'])
#            user.backend = 'django.contrib.auth.backends.ModelBackend'
#            auth.login(request,user)
#            return HttpResponseRedirect('/')
#        return func(request, *args, **kwargs)
#    return _deco

def logout(request):
    auth.logout(request)
    response = HttpResponseRedirect('/')
    response.delete_cookie('sso_token', domain=settings.SESSION_COOKIE_DOMAIN)
    return response

#@login_required
def health(request):
    return HttpResponse('ok')

def login(request):
    title = '单点登录'
    user = request.user
    passwd_url = settings.PASSWD_URL
    show_captcha = settings.SHOW_CAPTCHA
    back = request.GET.get('back')
    if not back: back = '/'
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        code = request.POST.get('code')
        if show_captcha:
            if not Captcha(request).check(code): 
                result = '验证码错误'
                return render_to_response('main/login.html',locals())
        user = auth.authenticate(username=username,password=password)
        if user is not None:
            auth.login(request,user)
            token_confirm = Token(settings.SECRET_KEY)
            token_key = '%s' % username
            token = token_confirm.generate_validate_token(token_key)
            #redirect_uri = '%s?token=%s' % (back, token)
            #return HttpResponseRedirect(redirect_uri)
            response = HttpResponseRedirect(back)
            response.set_cookie('sso_token', token, settings.COOKIE_EXPIRES,domain=settings.SESSION_COOKIE_DOMAIN)
            return response
        else:
            result = '用户名或密码错误'
    return render_to_response('main/login.html',locals())

def get_user(request):
    expiration = settings.COOKIE_EXPIRES
    token = request.GET.get('token')
    sso_dict = {}
    if token:
        token_confirm = Token(settings.SECRET_KEY)
        try:
            username = token_confirm.confirm_validate_token(token, expiration=expiration)
            ret = User.objects.filter(username=username)
            if ret:
                sso_dict['username'] = ret[0].username
                sso_dict['email'] = ret[0].email
                sso_dict['cn'] = ret[0].last_name
        except Exception as e:
            sso_dict['error'] = 'token error'
    else:
        sso_dict['error'] = 'args error'
    return HttpResponse(json.dumps(sso_dict))
