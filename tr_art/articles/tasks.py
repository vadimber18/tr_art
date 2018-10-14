import datetime

from django.core.mail import send_mail
from tr_art.celery import app
import articles.models


@app.task
def notify_new_article(article_id):
    ''' New order notify '''
    profiles = articles.models.UserProfile.objects.filter(role='translator')
    users = [p.user for p in profiles]
    article = articles.models.Article.objects.get(pk=article_id)
    for user in users:
        try:
            send_mail(
                'New article on Translate Articles!!!',
                'Hello, {}New order with source text: {} was just published! Check it! http://127.0.0.1:8000/order/{}/'.format(user.username, article.source_text, article.id),
                'email@email.com',
                [user.email],
                fail_silently=False,
            )
        except:
            pass

@app.task
def notify_update_article(article_id):
    ''' Accepted or finished order notify '''
    user = articles.models.Article.objects.get(pk=article_id).requester.user
    article = articles.models.Article.objects.get(pk=article_id)
    msg = ''
    if article.status == 1:
        msg = 'Hello, {}! Someone just accepted your order! Check it! http://127.0.0.1:8000/myorders/'.format(user.username)
    elif article.status == 2:
        msg = 'Hello, {}! The translator just finished your order! You can download it: http://127.0.0.1:8000/myorders/'.format(user.username)
    try:
        send_mail(
            'Status of your order was changed!',
            msg,
            'email@email.com',
            [user.email],
            fail_silently=False,
        )
    except:
        pass

@app.task
def notify_deadline_article():
    ''' Notify if translator got 3 or less days till deadline '''
    now = datetime.datetime.now()
    for a in articles.models.Article.objects.filter(status=1):
        try:
            days_to_deadline = (a.deadline.replace(tzinfo=None).date() - now.date()).days
            if days_to_deadline <= 3:
                send_mail(
                    'Its pretty close to deadline!',
                    'Hello, {}! Its only {} days till deadline of your accepted order! You can check your order: http://127.0.0.1:800/order/{}/'.format(a.translator.user.username,
                        days_to_deadline, a.id),
                    'email@email.com',
                    [a.translator.user.email],
                    fail_silently=False,
                )
        except:
            pass