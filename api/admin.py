from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from api.models import SubscriptionKeys, Subscriptions

# Register your models here.
admin.site.register(SubscriptionKeys)
admin.site.register(Subscriptions)