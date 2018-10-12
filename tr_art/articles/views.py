import datetime

from django.shortcuts import render, render_to_response
from django.views.generic import FormView, ListView, DetailView, View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django import forms
from django.http import HttpResponseRedirect, HttpResponse

from rest_framework import viewsets, generics, exceptions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from knox.views import LoginView as KnoxLoginView
from knox.auth import TokenAuthentication

from articles.models import UserProfile, ArtCategory, ArtLanguage, Article
from articles.forms import UserRegistrationForm, AddOrderForm, FreshOrdersForm, AcceptOrderForm, FinishOrderForm
from articles.serializers import UserSerializer, ArticleSerializer, ArticleIdSerializer, ArticleAcceptSerializer, UserProfileSerializer
from articles.art_funcs import *

class UserRegisterView(FormView):
    template_name = 'articles/register.html'

    def get(self, request, *args, **kwargs):
        form = UserRegistrationForm
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            username, email, password, role, redirect_to = get_register_cdata(form)
            create_userprofile_from_cdata(username, email, password, role)
            user = authenticate(username = username, password = password)
            login(request, user)
            return HttpResponseRedirect(redirect_to)
        return render(request, self.template_name, {'form': form})


class AddOrderView(FormView):
    """ Add new order as requester """
    template_name = 'articles/addorder.html'

    def get(self, request, *args, **kwargs):
        form = AddOrderForm
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = AddOrderForm(request.POST)
        if form.is_valid():
            user = request.user
            create_article_from_form(form, user)
            return HttpResponseRedirect('/myorders/')
        return render(request, self.template_name, {'form': form})

class FreshOrdersView(FormView):
    """ Displays all orders with status = 0 (pending) for translator """
    """ Form with category(topic id) filter """
    template_name = 'articles/freshorders.html'

    def get(self, request, *args, **kwargs):
        form = FreshOrdersForm(request.GET)
        if form.is_valid():
            top = form.cleaned_data['topic_id']
            topic_id = ArtCategory.objects.filter(id__in=top)
            if len(topic_id):
                articles = Article.objects.filter(status=0).filter(topic_id__in=topic_id).order_by('-reg_date')
                return render(request, self.template_name, {'form': form, 'articles': articles})
        articles = Article.objects.filter(status=0).order_by('reg_date')
        return render(request, self.template_name, {'form': form, 'articles': articles})

class OrderView(FormView): #only for translator (or not?)
    """ Displays concrete order for translator """
    """ If order status is 0 - translator can take order """
    """ If order status is 1 - translator can finish order, if he is article.requester """
    template_name = 'articles/order.html'

    def get(self, request, *args, **kwargs):
        article = Article.objects.get(id=kwargs['pk'])
        if article.status == 0:
            form = AcceptOrderForm
        elif article.status == 1 and article.translator == request.user.profile:
            form = FinishOrderForm
        else:
            return HttpResponseRedirect('/acceptedorders/')
        return render(request, self.template_name, {'form': form, 'article': article})

    def post(self, request, *args, **kwargs):
        article = Article.objects.get(id=kwargs['pk'])
        if article.status == 0:
            form = AcceptOrderForm(request.POST)
            if form.is_valid():
                deadline = form.cleaned_data['deadline']
                order_accept(article, deadline,request.user)
                return HttpResponseRedirect('/acceptedorders/')
        elif article.status == 1: #we dont check article.translator due POST
            form = FinishOrderForm(request.POST)
            if form.is_valid():
                target_text = form.cleaned_data['target_text']
                order_finish(article, target_text)
                return HttpResponseRedirect('/acceptedorders/')
        return render(request, self.template_name, {'form': form, 'article': article})

class OrderTargetTextView(View):
    """ Get full target_text for requester, who created request """
    def get(self, request, *args, **kwargs):
        article = Article.objects.get(id=kwargs['pk'])
        if article.status == 2 and article.requester == request.user.profile:
            return HttpResponse(article.target_text)
        return HttpResponseRedirect('/login/')

class AcceptedOrdersView(ListView):
    """ Displays all accepted by current translator orders """
    context_object_name = 'my_orders'
    template_name = 'articles/myorders.html'

    def get_queryset(self):
        user = self.request.user
        profile = UserProfile.objects.get(user=user)
        queryset = Article.objects.filter(translator=profile)
        return queryset

class MyOrdersView(ListView):
    """ Displays all own by current requester orders """
    context_object_name = 'my_orders'
    template_name = 'articles/myorders.html'

    def get_queryset(self):
        user = self.request.user
        userprofile = UserProfile.objects.get(user=user)
        queryset = Article.objects.filter(requester=userprofile)
        return queryset
### api

class LoginApiView(KnoxLoginView):
    """ Own auth class for process POST parameters, not auth (like -u username:password) """
    authentication_classes = [OwnBasicAuthentication]

class RegisterApiView(APIView):
    def post(self, request):
        params = request.data
        if all(x in params.keys() for x in ['username', 'email', 'role', 'password']):
            params.update({'user':{'username':params['username'],'email':params['email'],
                'password':params['password']}})
            serializer = UserProfileSerializer(data=params)
            if serializer.is_valid(raise_exception=ValueError):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise exceptions.ValidationError('Wrong parameters: username, email, role, password were expected')

class RequestsApiView(APIView):
    """ Get all the Articles (requests) """
    """ Create new Article (request) by requester """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        articles = Article.objects.order_by('-reg_date')
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)

    def post(self, request):
        request.data.update({'requester': request.user.profile.id})
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid(raise_exception=ValueError):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.error_messages, status=status.HTTP_404_BAD_REQUEST)

class PendingRequestsApiView(APIView):
    """ List all pending requests (status=0) """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        articles = Article.objects.filter(status=0).order_by('-reg_date')
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)

class RequestIdApiView(APIView):
    """ Get/delete request by id """
    """ Finish request by id, if translator accepted it before """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        article = Article.objects.filter(id=kwargs['pk'])
        if not len(article):
            raise exceptions.ValidationError('Request with this id didnt found')
        serializer = ArticleSerializer(article[0], many=False)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        article = Article.objects.filter(id=kwargs['pk'])
        if not len(article):
            raise exceptions.ValidationError('Request with this id didnt found')
        article[0].delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, *args, **kwargs):
        article = Article.objects.filter(id=kwargs['pk'])
        if not len(article):
            raise exceptions.ValidationError('Request with this id didnt found')
        request.data.update({'translator': request.user.profile.id})
        serializer = ArticleIdSerializer(instance=article[0], data=request.data)#, \
        if serializer.is_valid(raise_exception=ValueError):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.error_messages, status=status.HTTP_404_BAD_REQUEST)

class RequestAcceptApiView(APIView):
    """ Accept pending (status = 0) request by requester """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        if (request.user.profile.role != 'translator'):
            raise exceptions.ValidationError('Only translators can do that!')
        article = Article.objects.filter(id=kwargs['pk'])
        if not len(article):
            raise exceptions.ValidationError('Request with this id didnt found')
        request.data.update({'translator': request.user.profile.id})
        serializer = ArticleAcceptSerializer(instance=article[0], data=request.data)#, \
        if serializer.is_valid(raise_exception=ValueError):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.error_messages, status=status.HTTP_404_BAD_REQUEST)


class UserListApiView(APIView):
    """ List of all users """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        profiles = UserProfile.objects.all()
        serializer = UserProfileSerializer(profiles, many=True)
        return Response(serializer.data)

class UserApiView(APIView):
    """ User by id """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        profile = UserProfile.objects.filter(id=kwargs['pk'])
        if not len(profile):
            raise exceptions.ValidationError('No user with this id')
        serializer = UserProfileSerializer(profile[0], many=False)
        return Response(serializer.data)

class UserRequestsApiView(APIView):
    """ List of users requests by users id, user must be requester """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        profile = UserProfile.objects.filter(id=kwargs['pk'])
        if not len(profile):
            raise exceptions.ValidationError('No user with this id')
        serializer = ArticleSerializer(profile[0].my_articles.all().order_by('-reg_date'), many=True)
        return Response(serializer.data)