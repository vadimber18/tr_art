from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name='profile')
    role = models.TextField() #requester, translator

    def get_username(self):
        return (self.user.username)

    def get_email(self):
        return (self.user.email)

    def get_first_name(self):
        return (self.user.first_name)

    def get_last_name(self):
        return (self.user.last_name)

    def __str__(self):
        return (self.user.username)

class ArtCategory(models.Model):
    name = models.TextField()

    def __str__(self):
        return (self.name)

class ArtLanguage(models.Model):
    name = models.TextField()

    def __str__(self):
        return (self.name)

class Article(models.Model):
    requester = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='my_articles')
    source_text = models.TextField()
    topic_id = models.ManyToManyField(ArtCategory)
    source_language = models.ForeignKey(ArtLanguage, on_delete=models.CASCADE, related_name='sarticles')
    target_language = models.ManyToManyField(ArtLanguage)
    status = models.IntegerField() #0 pending 1 got translator 2 done
    reg_date = models.DateTimeField()
    translator = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='accepted_article')
    target_text = models.TextField(null=True)
    deadline = models.DateTimeField(null=True)
    done_date = models.DateTimeField(null=True)

    def __str__(self):
        return (self.source_text[:10])