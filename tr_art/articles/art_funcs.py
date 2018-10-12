import datetime
import json

from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions

from articles.models import ArtLanguage, ArtCategory, Article, UserProfile


def create_article_from_form(form, user):
    source_text = form.cleaned_data['source_text']
    top = form.cleaned_data['topic_id']
    topic_id = ArtCategory.objects.filter(id__in=top)
    source_language = form.cleaned_data['source_language']
    source_language = ArtLanguage.objects.get(id=source_language)
    tar_lang = form.cleaned_data['target_language']
    target_language = ArtLanguage.objects.filter(id__in=tar_lang)
    status = 0
    reg_date = datetime.datetime.now()
    requester = UserProfile.objects.get(user = user)
    a = Article(requester=requester, source_text=source_text,
    source_language=source_language, status=0, reg_date=reg_date)
    a.save()
    for c in topic_id:
        a.topic_id.add(c)
    for t in target_language:
        a.target_language.add(t)
    a.save()

def get_register_cdata(form):
    account_type = form.cleaned_data['account_type']
    if account_type == '0':
        role = 'translator'
        redirect_to = '/freshorders/'
    else:
        role = 'requester'
        redirect_to = '/myorders/'
    return form.cleaned_data['username'], form.cleaned_data['email'], \
        form.cleaned_data['password'], role, redirect_to


def order_accept(article, deadline, user):
    article.status = 1
    article.translator = user.profile
    article.deadline = deadline
    article.save()

def order_finish(article, target_text):
    article.status = 2
    article.done_date = datetime.datetime.now()
    article.target_text = target_text
    article.save()

def create_userprofile_from_cdata(username, email, password, role):
    # returns user, not userprofile
    user = User.objects.create_user(username, email, password)
    profile = UserProfile(user=user, role=role)
    profile.save()
    return user

def requester_test(user):
    try:
        return user.profile.role == 'requester'
    except:
        return False

def translator_test(user):
    try:
        return user.profile.role == 'translator'
    except:
        return False


class OwnBasicAuthentication(authentication.BasicAuthentication):
    def authenticate(self, request):
        params = request.data
        if 'username' in params.keys() and 'password' in params.keys():
            userid, password = params['username'], params['password']
            return self.authenticate_credentials(userid, password, request)
        else:
            msg = 'Wrong parameters: username, password were expected '
            raise exceptions.ValidationError(msg)
