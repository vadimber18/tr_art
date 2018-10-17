import datetime
import json

from django.test import RequestFactory, TestCase, Client
from rest_framework import status
from rest_framework.test import APITestCase

from django.contrib.auth.models import User
from articles.models import UserProfile, ArtCategory, ArtLanguage, Article
from articles.forms import UserRegistrationForm, AddOrderForm
from articles.views import *
from articles.serializers import *

#models

class UserProfileTest(TestCase):
    fixtures = ['user.json', 'userprofile.json']

    def setUp(self):
        pass

    def test_methods(self):
        tra1 = UserProfile.objects.get(user__username='tra1')
        req1 = UserProfile.objects.get(user__username='req1')
        self.assertEqual(tra1.get_username(), tra1.user.username)
        self.assertEqual(tra1.get_email(), tra1.user.email)
        self.assertEqual(tra1.get_first_name(), tra1.user.first_name)
        self.assertEqual(tra1.get_last_name(), tra1.user.last_name)
        self.assertEqual(req1.get_username(), req1.user.username)
        self.assertEqual(req1.get_email(), req1.user.email)
        self.assertEqual(req1.get_first_name(), req1.user.first_name)
        self.assertEqual(req1.get_last_name(), req1.user.last_name)

#forms

class UserRegistrationFormTest(TestCase):
    fixtures = ['user.json', 'userprofile.json']

    def setUp(self):
        pass

    def test_form(self):
        form_data = {'username':'tra1', 'email':'tra1@tra.tra',
            'password':'qwerty', 'account_type':0}
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())       #username exists
        form_data.update({'username':'tra3'})
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())       #email exists
        form_data.update({'email':'tra3@tra.tra'})
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())	#ok
        form_data.update({'email':'tra3tra.tra'})
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())       #bad email
        form_data.update({'email':'tra3@tratra'})
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())       #bad email
        form_data.update({'email':'tra3@tra.tra', 'password':''})
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())       #no password
        form_data.update({'username':''})
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())       #no username
        form_data.update({'username':'tra2', 'account_type':2})
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())       #no such account_type

class AddOrderFormTest(TestCase):
    fixtures = ['artcategory.json', 'artlanguage.json']

    def setUp(self):
        pass

    def test_form(self):
        form_data = {'source_text':'Some source text', 'topic_id':[1,2,3], 
            'source_language':1, 'target_language':[2,3,4]}
        form = AddOrderForm(data=form_data)
        self.assertTrue(form.is_valid())
        form_data.update({'source_text':''})
        form = AddOrderForm(data=form_data)
        self.assertFalse(form.is_valid())	#no source_text
        form_data.update({'source_text':'Some source text', 'topic_id':[1,2,3,4,5,6]})
        form = AddOrderForm(data=form_data)
        self.assertFalse(form.is_valid())	#no such topic_id
        form_data.update({'topic_id':[1,2,3], 'target_language':[8,9]})
        form = AddOrderForm(data=form_data)
        self.assertFalse(form.is_valid())	#no such target_language
        form_data.update({'target_language':[2,3,4], 'source_language':9})
        form = AddOrderForm(data=form_data)
        self.assertFalse(form.is_valid())	#no such source_language

#views

class RegisterOrderViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_access(self):
        request = self.factory.get('/register/')
        response = UserRegisterView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        profile_count = UserProfile.objects.count()
        request = self.factory.post('/register/', {'username':'tra3', 'email':'tra3@tra.tra',
            'password':'qwerty', 'account_type': 0})
        from django.contrib.messages.middleware import MessageMiddleware
        from django.contrib.sessions.middleware import SessionMiddleware
        SessionMiddleware().process_request(request)
        MessageMiddleware().process_request(request)
        response = UserRegisterView.as_view()(request)
        self.assertEqual(profile_count + 1, UserProfile.objects.count())

class ArticleViewsTest(TestCase):
    fixtures = ['user.json', 'userprofile.json', 'artlanguage.json', 'artcategory.json',
        'article.json']

    def setUp(self):
        self.factory = RequestFactory()
        self.tra1 = UserProfile.objects.get(user__username='tra1')
        self.tra2 = UserProfile.objects.get(user__username='tra2')
        self.req1 = UserProfile.objects.get(user__username='req1')
        self.req2 = UserProfile.objects.get(user__username='req2')

    def test_access(self):
        ''' Using client, not factory to test view decorators from urls.py '''
        response = self.client.login(username='req1', password='asdfgh')
        response = self.client.get('/addorder/')
        self.assertEqual(200, response.status_code)
        response = self.client.get('/myorders/')
        self.assertEqual(200, response.status_code)
        response = self.client.get('/freshorders/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/acceptedorders/')
        self.assertEqual(302, response.status_code)

        # requester got acces to only his finished orders text
        response = self.client.get('/order/1/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/order/2/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/order/3/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/order/1/target_text/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/order/2/target_text/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/order/3/target_text/')
        self.assertEqual(200, response.status_code)

        response = self.client.login(username='req2', password='asdfgh')
        response = self.client.get('/order/3/target_text/')
        self.assertEqual(302, response.status_code)

        response = self.client.login(username='tra1', password='qwerty')
        response = self.client.get('/addorder/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/myorders/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/freshorders/')
        self.assertEqual(200, response.status_code)
        response = self.client.get('/acceptedorders/')
        self.assertEqual(200, response.status_code)

        # translator got acces to only pending orders and his orders with status=1
        response = self.client.get('/order/1/')
        self.assertEqual(200, response.status_code)
        response = self.client.get('/order/2/')
        self.assertEqual(200, response.status_code)
        response = self.client.get('/order/3/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/order/1/target_text/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/order/2/target_text/')
        self.assertEqual(302, response.status_code)
        response = self.client.get('/order/3/target_text/')
        self.assertEqual(302, response.status_code)

        response = self.client.login(username='tra2', password='qwerty')
        response = self.client.get('/order/1/')
        self.assertEqual(200, response.status_code)
        response = self.client.get('/order/2/')
        self.assertEqual(302, response.status_code)

    def test_addorder(self):
	''' Adds order by requester, then checks if translator see it '''
        article_count = Article.objects.count()
        request = self.factory.post('/addorder/', {'source_text': 'some new source text', 'topic_id': [1],
            'source_language': 1, 'target_language': [2,3]})
        request.user = self.req1.user
        response = AddOrderView.as_view()(request)
        post_article_count = Article.objects.count()
        self.assertEqual(article_count + 1, post_article_count)
        self.client.login(username='tra1', password='qwerty')
        response = self.client.get('/freshorders/')
        articles = response.context['articles']
        self.assertEqual(True, len([x for x in articles if x.source_text == 'some new source text']))
        response = self.client.get('/order/4/')
        self.assertEqual(200, response.status_code)

    def test_acceptorder(self):
	''' Accepts order by translator, checks it at /acceptedorders and at /myorders as requester '''
        article_count = Article.objects.filter(status=1).count()
        request = self.factory.post('/order/1/', {'deadline': '2018-10-16 20:05:16'})
        request.user = self.tra1.user
        response = OrderView.as_view()(request, pk=1)
        post_article_count = Article.objects.filter(status=1).count()
        self.assertEqual(article_count + 1, post_article_count)
        self.client.login(username='tra1', password='qwerty')
        response = self.client.get('/acceptedorders/')
        articles = response.context['my_orders']
        self.assertEqual(True, len([x for x in articles if x.source_text == 'First source text']))
        response = self.client.get('/order/1/')
        self.assertEqual(200, response.status_code)
        self.client.login(username='req1', password='asdfgh')
        response = self.client.get('/myorders/')
        articles = response.context['my_orders']
        self.assertEqual(True, len([x for x in articles if x.source_text == 'First source text' and x.status == 1]))

    def test_finishorder(self):
	''' Finishes order by translator, then checks it at /acceptedorders and /myorders, target_text by requester '''
        article_count = Article.objects.filter(status=2).count()
        request = self.factory.post('/order/2/', {'target_text': 'Second target text'})
        request.user = self.tra1.user
        response = OrderView.as_view()(request, pk=2)
        post_article_count = Article.objects.filter(status=2).count()
        self.assertEqual(article_count + 1, post_article_count)
        self.client.login(username='tra1', password='qwerty')
        response = self.client.get('/acceptedorders/')
        articles = response.context['my_orders']
        self.assertTrue(len([x for x in articles if x.target_text == 'Second target text']))
        response = self.client.get('/order/2/')
        self.assertEqual(302, response.status_code)
        self.client.login(username='req1', password='asdfgh')
        response = self.client.get('/myorders/')
        articles = response.context['my_orders']
        self.assertTrue(len([x for x in articles if x.target_text == 'Second target text']))
        response = self.client.get('/order/2/target_text/')
        self.assertEqual(200, response.status_code)

#api

def check_login_keys(json_data):
    keys1 = ['user', 'token']
    keys2 = ['username', 'email', 'first_name', 'last_name']
    if all(i in keys1 for i in json_data):
        if all(j in keys2 for j in json_data['user']):
            return True
    return False

class APITests(APITestCase):
    fixtures = ['user.json', 'userprofile.json', 'artlanguage.json', 'artcategory.json',
        'article.json']

    def test_login(self, username='tra1', password='qwerty'):
        response = self.client.post('/auth/login/', json.dumps({'username': username, 'password': password}),
            content_type = 'application/json')
        json_data = json.loads(response.content)
        self.token = json_data['token']
        self.assertTrue(check_login_keys(json_data))

    def test_register(self):
        response = self.client.post('/auth/register/', json.dumps({'username': 'tra3', 'password': 'qwerty',
            'email': 'tra3@tra.tra', 'role': 'translator'}), content_type = 'application/json')
        self.assertTrue(all(i in ['username', 'email', 'first_name', 'last_name', 'role'] for i in 
            json.loads(response.content)))

    def test_getrequests(self):
        self.test_login('tra1', 'qwerty')
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.get('/requests/', content_type='application/json')
        self.assertTrue(
            all(i in ['First source text', 'Second source text', 'Third source text'] for i in
                [x['source_text'] for x in json.loads(response.content)])
        )

    def test_postrequests(self):
        self.test_login('req1', 'asdfgh')
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.post('/requests/', json.dumps({'source_text':'Fourth source text',
            'source_language': 1, 'target_language': [2,3], 'topic_id': [2]}),
            content_type='application/json')
        self.assertTrue('Fourth source text' in json.loads(response.content)['source_text'])

    def test_getpending(self):
        self.test_login('tra1', 'qwerty')
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.get('/requests/pending/', content_type='application/json')
        self.assertTrue(all(article['status'] == 0 for article in json.loads(response.content)))

    def test_getrequestid(self):
        self.test_login('tra1', 'qwerty')
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.get('/requests/3/', content_type='application/json')
        self.assertTrue(json.loads(response.content)['source_text'] == 'Third source text')

    def test_delrequestid(self):
        self.test_login('tra1', 'qwerty')
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.delete('/requests/3/', content_type='application/json')
        self.assertFalse(Article.objects.filter(source_text='Third source text').count())

    def test_postrequestid(self): # finish order by id
        self.test_login('tra1', 'qwerty')
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.post('/requests/2/', json.dumps({'target_text':'Second target text'}), 
            content_type='application/json')
        self.assertTrue(Article.objects.filter(status=2, target_text='Second target text', source_text='Second source text').count())

    def test_postrequestaccept(self):
        self.test_login('tra1', 'qwerty')
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.post('/requests/1/accept/', json.dumps({'deadline':'2018-12-31T23:03'}),
            content_type='application/json')
        self.assertTrue(Article.objects.filter(status=1, source_text='First source text').count())

    def test_getusers(self):
        self.test_login('tra1', 'qwerty')
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.get('/users/', content_type='application/json')
        self.assertEqual(UserProfile.objects.count(), len(json.loads(response.content)))

    def test_getuserid(self):
        self.test_login('tra1', 'qwerty')
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.get('/users/1/', content_type='application/json')
        self.assertTrue(json.loads(response.content) == {'username':'tra1', 'email':'tra1@tra.tra',
            'first_name':'', 'last_name':'', 'role':'translator'})

    def test_getuseridrequests(self):
        self.test_login('tra1', 'qwerty')
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + self.token)
        response = self.client.get('/users/3/requests/', content_type='application/json')
        self.assertTrue(all(u['requester'] == 3 for u in json.loads(response.content)))
