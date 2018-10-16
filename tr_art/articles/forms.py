import datetime

from django import forms

from articles.models import *

class UserRegistrationForm(forms.Form):
    username = forms.CharField(
        required = True,
        label = 'Username',
        max_length = 32
    )
    email = forms.EmailField(
        required = True,
        label = 'Email',
        max_length = 32,
    )
    password = forms.CharField(
        required = True,
        label = 'Password',
        max_length = 32,
        widget = forms.PasswordInput()
    )
    account_type = forms.ChoiceField(choices = 
        ((0, 'Translator (Исполнитель)'),(1, 'Requester (Заказчик)')))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("User with this username already exists")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("User with this email already exists")
        return email


class AddOrderForm(forms.Form):
    source_text = forms.CharField(widget=forms.Textarea, required = True)
    topic_id = forms.MultipleChoiceField(choices = [], 
        widget=forms.widgets.SelectMultiple(attrs={'size':10}), required = True)
    source_language = forms.ChoiceField(choices = [], required = True)
    target_language = forms.MultipleChoiceField(choices = [], 
        widget=forms.widgets.SelectMultiple(attrs={'size':10}), required = True)

    def __init__(self, *args, **kwargs):
        super(AddOrderForm, self).__init__(*args, **kwargs)
        self.fields['topic_id'].choices = [(c[0], c[1]) for c in ArtCategory.objects.all().values_list('id', 'name')]
        self.fields['source_language'].choices = [(s[0], s[1]) for s in ArtLanguage.objects.all().values_list('id', 'name')]
        self.fields['target_language'].choices = [(t[0], t[1]) for t in ArtLanguage.objects.all().values_list('id', 'name')]

class FreshOrdersForm(forms.Form):
    topic_id = forms.MultipleChoiceField(choices = [],
        widget=forms.widgets.SelectMultiple(attrs={'size':10}), required = False)

    def __init__(self, *args, **kwargs):
        super(FreshOrdersForm, self).__init__(*args, **kwargs)
        self.fields['topic_id'].choices = [(c[0], c[1]) for c in ArtCategory.objects.all().values_list('id', 'name')]

class AcceptOrderForm(forms.Form):
    deadline = forms.DateTimeField(initial=datetime.datetime.now, required = True)

class FinishOrderForm(forms.Form):
    target_text = forms.CharField(widget=forms.Textarea, required = True)