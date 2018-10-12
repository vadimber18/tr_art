from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import path, re_path
from django.conf.urls import include

from rest_framework import routers

from articles.views import *
from articles.art_funcs import requester_test, translator_test

from knox import views as knox_views


urlpatterns = [
    path('admin/', admin.site.urls),
    re_path('^login/$', auth_views.login, {'template_name':
        'articles/login.html'}, name='loginview'),
    re_path(r'^logout/$', auth_views.logout, {'template_name':
        'articles/logout.html'}, name='logoutview'),
    re_path(r'^register/$', UserRegisterView.as_view(), name='registerview'),
    re_path(r'^addorder/$', user_passes_test(requester_test,login_url='/login')(AddOrderView.as_view()), name='addorderview'),
    re_path(r'^myorders/$', user_passes_test(requester_test,login_url='/login')(MyOrdersView.as_view()), name='myordersview'),
    re_path(r'^freshorders/$', user_passes_test(translator_test,login_url='/login')(FreshOrdersView.as_view()), name='freshordersview'),
    re_path(r'^acceptedorders/$', user_passes_test(translator_test,login_url='/login')(AcceptedOrdersView.as_view()), name='acceptedordersview'),
    re_path(r'^order/(?P<pk>\d+)/$', user_passes_test(translator_test,login_url='/login')(OrderView.as_view()), name='orderview'),
    re_path(r'^order/(?P<pk>\d+)/target_text/$', user_passes_test(requester_test,login_url='/login')(OrderTargetTextView.as_view()), 
            name='ordertargettext'),
    #api
    re_path(r'^auth/login/$', LoginApiView.as_view(), name='knox_login'),
    re_path(r'^auth/logout/$', knox_views.LogoutView.as_view(), name='knox_logout'),
    re_path(r'^auth/logoutall/$', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
    re_path(r'^auth/register/$', RegisterApiView.as_view()),
    re_path(r'^requests/$', RequestsApiView.as_view()),
    re_path(r'^requests/pending/$', PendingRequestsApiView.as_view()),
    re_path(r'^requests/(?P<pk>\d+)/$', RequestIdApiView.as_view()),
    re_path(r'^requests/(?P<pk>\d+)/accept/$', RequestAcceptApiView.as_view()),
    re_path(r'^users/$', UserListApiView.as_view()),
    re_path(r'^users/(?P<pk>\d+)/$', UserApiView.as_view()),
    re_path(r'^users/(?P<pk>\d+)/requests/$', UserRequestsApiView.as_view()),
]
