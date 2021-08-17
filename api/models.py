from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Group
from django.contrib.auth.models import User

# Create your models here.

# model for keys used to add subscriptions
class SubscriptionKeys(models.Model):
    key = models.CharField(max_length=36)

# subscription table, containing everyone that has a subscription with the following data: their user, their token and when their subscription started
# and when it ends
class Subscriptions(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    token = models.OneToOneField(Token, on_delete=models.CASCADE)
    subscription_start = models.DateField()
    subscription_end = models.DateField()

"""
# TOKEN MODEL ---------------------------------------
# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
        # Group.objects.get(name="premium").user_set.add(instance)
"""